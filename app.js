// Schmitzter – App-Logik
//
// Ablauf: Startseite -> "QR-Code scannen" (Kamera + jsQR) -> Karte gefunden
// -> Play -> Song ab chorusStart, laeuft PLAY_DURATION_MS. Waehrend der
// Wiedergabe kann jederzeit aufgedeckt werden (Titel/Interpret/Jahr), der
// Ausschnitt laeuft dabei einfach bis zum vorgesehenen Ende weiter. Danach
// "Naechste Karte" -> Kamera oeffnet sich direkt wieder fuer den naechsten
// Scan.
//
// Der YouTube-Player wird einmalig erzeugt und fuer jede neue Karte per
// cueVideoById() wiederverwendet (statt destroy/recreate), damit der
// iOS-Autoplay-Trick (Player existiert schon vor dem Klick) auch bei der
// zweiten, dritten, ... Karte weiter funktioniert.

const PLAY_DURATION_MS = 22000; // 20-25 Sekunden

const loadingEl = document.getElementById("loading");
const homeEl = document.getElementById("home");
const scannerEl = document.getElementById("scanner");
const errorEl = document.getElementById("error");
const errorTextEl = document.getElementById("errorText");
const gameEl = document.getElementById("game");

const scanBtn = document.getElementById("scanBtn");
const scanVideoEl = document.getElementById("scanVideo");
const scanHintEl = document.getElementById("scanHint");
const cancelScanBtn = document.getElementById("cancelScanBtn");
const errorBackBtn = document.getElementById("errorBackBtn");

const playBtn = document.getElementById("playBtn");
const revealBtn = document.getElementById("revealBtn");
const nextBtn = document.getElementById("nextBtn");
const resultEl = document.getElementById("result");
const resultYearEl = document.getElementById("resultYear");
const resultTitleEl = document.getElementById("resultTitle");
const resultArtistEl = document.getElementById("resultArtist");

let songsCache = null;
let song = null;
let player = null;
let playerReady = false;
let apiReady = false;
let pendingPlay = false;
let pendingSong = null;
let revealTimer = null;

let videoStream = null;
let scanRAF = null;
const scanCanvas = document.createElement("canvas");
const scanCtx = scanCanvas.getContext("2d", { willReadFrequently: true });

function showState(state) {
  [loadingEl, homeEl, scannerEl, errorEl, gameEl].forEach((el) =>
    el.classList.add("hidden")
  );
  state.classList.remove("hidden");
}

function showError(message) {
  stopScanner();
  errorTextEl.textContent = message;
  showState(errorEl);
}

async function loadSongsData() {
  if (songsCache) return songsCache;
  const res = await fetch("songs.json", { cache: "no-store" });
  if (!res.ok) throw new Error("songs.json nicht erreichbar");
  songsCache = await res.json();
  return songsCache;
}

function extractIdFromScan(text) {
  try {
    const url = new URL(text);
    const id = url.searchParams.get("id");
    if (id) return id;
  } catch (err) {
    // kein vollstaendiger URL-Text -> direkt als ID interpretieren
  }
  return text.trim();
}

async function loadSong(id) {
  showState(loadingEl);

  if (!id) {
    showError("Kein gueltiger QR-Code erkannt.");
    return;
  }

  let songs;
  try {
    songs = await loadSongsData();
  } catch (err) {
    showError("Songdaten konnten nicht geladen werden.");
    return;
  }

  const found = songs.find((s) => s.id === id);
  if (!found) {
    showError("Diese Karte ist unbekannt (ungueltige ID).");
    return;
  }

  resetRoundState();
  song = found;
  showState(gameEl);
  prepareVideo();
}

function resetRoundState() {
  if (revealTimer) {
    clearTimeout(revealTimer);
    revealTimer = null;
  }
  pendingPlay = false;
  playBtn.disabled = false;
  playBtn.textContent = "▶ Abspielen";
  revealBtn.classList.add("hidden");
  nextBtn.classList.add("hidden");
  resultEl.classList.add("hidden");
}

// --- YouTube Player -------------------------------------------------------

window.onYouTubeIframeAPIReady = function () {
  apiReady = true;
  if (pendingSong) {
    const s = pendingSong;
    pendingSong = null;
    prepareVideo(s);
  }
};

function prepareVideo() {
  if (!apiReady) {
    pendingSong = song;
    return;
  }

  if (!player) {
    player = new YT.Player("player", {
      height: "90",
      width: "160",
      videoId: song.youtubeId,
      playerVars: {
        start: song.chorusStart,
        controls: 0,
        modestbranding: 1,
        rel: 0,
        fs: 0,
        iv_load_policy: 3,
        disablekb: 1,
        playsinline: 1,
        origin: window.location.origin,
      },
      events: {
        onReady: onPlayerReady,
        onStateChange: onPlayerStateChange,
        onError: onPlayerError,
      },
    });
  } else {
    player.cueVideoById({
      videoId: song.youtubeId,
      startSeconds: song.chorusStart,
    });
  }
}

function onPlayerReady() {
  playerReady = true;
  if (pendingPlay) {
    pendingPlay = false;
    startVideoPlayback();
  }
}

function startVideoPlayback() {
  player.seekTo(song.chorusStart, true);
  player.playVideo();
}

function startPlayback() {
  playBtn.disabled = true;
  playBtn.textContent = "Laedt …";

  if (playerReady) {
    startVideoPlayback();
  } else {
    pendingPlay = true;
  }
}

// Manche (monetarisierten) YouTube-Videos zeigen vor dem eigentlichen
// Inhalt eine Werbeanzeige. Die IFrame API meldet dafuer ebenfalls
// PLAYING, aber die Wiedergabeposition liegt dann nahe 0 statt bei
// chorusStart. Nur wenn die Position zum erwarteten Refrain passt,
// starten wir Countdown und Aufdecken-Button.
const AD_POSITION_TOLERANCE_SEC = 5;

function onPlayerStateChange(event) {
  if (event.data !== YT.PlayerState.PLAYING || revealTimer) return;

  const current = player.getCurrentTime();
  const isProbablyAd =
    Math.abs(current - song.chorusStart) > AD_POSITION_TOLERANCE_SEC;

  if (isProbablyAd) {
    // Warten, bis die Werbung durch ist; danach kommt ein neues
    // PLAYING-Event fuer den eigentlichen Song.
    return;
  }

  playBtn.textContent = "Laeuft …";
  revealBtn.classList.remove("hidden");
  revealTimer = setTimeout(() => {
    player.pauseVideo();
  }, PLAY_DURATION_MS);
}

const YT_ERROR_MESSAGES = {
  2: "ungueltige Video-ID",
  5: "HTML5-Player-Fehler",
  100: "Video nicht gefunden/entfernt",
  101: "Embedding vom Rechteinhaber gesperrt",
  150: "Embedding vom Rechteinhaber gesperrt",
};

function onPlayerError(event) {
  const code = event.data;
  const reason = YT_ERROR_MESSAGES[code] || "unbekannter Grund";
  showError(`Dieses Video kann nicht abgespielt werden (Code ${code}: ${reason}).`);
}

function reveal() {
  resultYearEl.textContent = song.year;
  resultTitleEl.textContent = song.title;
  resultArtistEl.textContent = song.artist;

  revealBtn.classList.add("hidden");
  resultEl.classList.remove("hidden");
  nextBtn.classList.remove("hidden");
}

// --- QR-Scanner (Kamera + jsQR) -------------------------------------------

async function startScanner() {
  showState(scannerEl);
  scanHintEl.textContent = "Karte in den Rahmen halten …";

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    showError(
      "Kamera-Zugriff wird von diesem Browser nicht unterstuetzt, oder die Seite laeuft nicht ueber eine sichere Verbindung (HTTPS/localhost)."
    );
    return;
  }

  try {
    videoStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: "environment" } },
      audio: false,
    });
  } catch (err) {
    showError(
      "Kein Kamera-Zugriff moeglich. Bitte die Kamera-Berechtigung im Browser erlauben und erneut versuchen."
    );
    return;
  }

  scanVideoEl.srcObject = videoStream;
  try {
    await scanVideoEl.play();
  } catch (err) {
    showError("Kamera-Vorschau konnte nicht gestartet werden.");
    return;
  }

  scanLoop();
}

function stopScanner() {
  if (scanRAF) {
    cancelAnimationFrame(scanRAF);
    scanRAF = null;
  }
  if (videoStream) {
    videoStream.getTracks().forEach((track) => track.stop());
    videoStream = null;
  }
  scanVideoEl.srcObject = null;
}

function scanLoop() {
  if (scanVideoEl.readyState === scanVideoEl.HAVE_ENOUGH_DATA) {
    scanCanvas.width = scanVideoEl.videoWidth;
    scanCanvas.height = scanVideoEl.videoHeight;
    scanCtx.drawImage(scanVideoEl, 0, 0, scanCanvas.width, scanCanvas.height);

    const imageData = scanCtx.getImageData(
      0,
      0,
      scanCanvas.width,
      scanCanvas.height
    );
    const code = jsQR(imageData.data, imageData.width, imageData.height, {
      inversionAttempts: "dontInvert",
    });

    if (code && code.data) {
      const id = extractIdFromScan(code.data);
      stopScanner();
      loadSong(id);
      return;
    }
  }
  scanRAF = requestAnimationFrame(scanLoop);
}

// --- Init ------------------------------------------------------------------

function init() {
  const params = new URLSearchParams(window.location.search);
  const id = params.get("id");

  if (id) {
    loadSong(id);
    return;
  }

  showState(homeEl);
}

scanBtn.addEventListener("click", startScanner);
cancelScanBtn.addEventListener("click", () => {
  stopScanner();
  showState(homeEl);
});
errorBackBtn.addEventListener("click", () => {
  showState(homeEl);
});

playBtn.addEventListener("click", startPlayback);
revealBtn.addEventListener("click", reveal);
nextBtn.addEventListener("click", () => {
  if (player) {
    player.pauseVideo();
  }
  resetRoundState();
  startScanner();
});

init();
