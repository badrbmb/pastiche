// Countdown timer script
function startCountdown(duration, display) {
    var timer = duration, hours, minutes, seconds;
    setInterval(function () {   
        hours = parseInt(timer / 3600, 10);
        minutes = parseInt((timer % 3600) / 60, 10);
        seconds = parseInt(timer % 60, 10);

        hours = hours < 10 ? "0" + hours : hours;
        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;

        display.textContent = "Next Wordle: " + hours + ":" + minutes + ":" + seconds;

        if (--timer < 0) {
            timer = duration;
        }
    }, 1000);
}

window.onload = function () {
    var countdownTime = 23 * 3600 + 59 * 60 + 59; // 9 hours, 43 minutes, 2 seconds
    var display = document.querySelector('#countdown');
    startCountdown(countdownTime, display);
};
