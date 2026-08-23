// Hitster DIY – Player-Logik
// Ablauf: Play -> Song ab chorusStart fuer PLAY_DURATION_MS -> Auto-Pause -> Aufdecken

const PLAY_DURATION_MS = 22000; // 20-25 Sekunden

const loadingEl = document.getElementById("loading");
const errorEl = document.getElementById("error");
const errorTextEl = document.getElementById("errorText");
const gameEl = document.getElementById("game");
const playBtn = document.getElementById("playBtn");
const playerWrap = document.getElementById("playerWrap");
const revealBtn = document.getElementById("revealBtn");
const resultEl = document.getElementById("result");
const resultYearEl = document.getElementById("resultYear");
const resultTitleEl = document.getElementById("resultTitle");
const resultArtistEl = document.getElementById("resultArtist");

let song = null;
let player = null;
let apiReady = false;
let revealTimer = null;

function showState(state) {
  loadingEl.classList.add("hidden");
  errorEl.classList.add("hidden");
  gameEl.classList.add("hidden");
  state.classList.remove("hidden");
}

function showError(message) {
  errorTextEl.textContent = message;
  showState(errorEl);
}

async function init() {
  const params = new URLSearchParams(window.location.search);
  const id = params.get("id");

  if (!id) {
    showError("Kein QR-Code erkannt (fehlende ID in der URL).");
    return;
  }

  let songs;
  try {
    const res = await fetch("songs.json", { cache: "no-store" });
    if (!res.ok) throw new Error("songs.json nicht erreichbar");
    songs = await res.json();
  } catch (err) {
    showError("Songdaten konnten nicht geladen werden.");
    return;
  }

  song = songs.find((s) => s.id === id);

  if (!song) {
    showError("Diese Karte ist unbekannt (ungueltige ID).");
    return;
  }

  showState(gameEl);
}

// Wird von der YouTube IFrame API global aufgerufen, sobald sie bereit ist.
window.onYouTubeIframeAPIReady = function () {
  apiReady = true;
};

function waitForApi(callback) {
  if (apiReady && window.YT && window.YT.Player) {
    callback();
    return;
  }
  const check = setInterval(() => {
    if (apiReady && window.YT && window.YT.Player) {
      clearInterval(check);
      callback();
    }
  }, 100);
}

function startPlayback() {
  playBtn.disabled = true;
  playBtn.textContent = "Laedt …";

  waitForApi(() => {
    playerWrap.classList.remove("hidden");

    player = new YT.Player("player", {
      height: "90",
      width: "160",
      videoId: song.youtubeId,
      playerVars: {
        autoplay: 1,
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
        onStateChange: onPlayerStateChange,
        onError: onPlayerError,
      },
    });
  });
}

function onPlayerStateChange(event) {
  if (event.data === YT.PlayerState.PLAYING && !revealTimer) {
    playBtn.textContent = "Laeuft …";
    revealTimer = setTimeout(() => {
      player.pauseVideo();
      showRevealButton();
    }, PLAY_DURATION_MS);
  }
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

function showRevealButton() {
  playerWrap.classList.add("hidden");
  revealBtn.classList.remove("hidden");
}

function reveal() {
  resultYearEl.textContent = song.year;
  resultTitleEl.textContent = song.title;
  resultArtistEl.textContent = song.artist;

  revealBtn.classList.add("hidden");
  resultEl.classList.remove("hidden");
}

playBtn.addEventListener("click", startPlayback);
revealBtn.addEventListener("click", reveal);

init();
