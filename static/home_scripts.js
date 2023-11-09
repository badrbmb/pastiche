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

        display.textContent = hours + "hrs " + minutes + "min " + seconds + "s";

        if (--timer < 0) {
            timer = duration;
        }
    }, 1000);
}

function loadValueDates() {
    // Retrieve valueDates from localstorage and parse into JSON
    let valueDatesString = localStorage.getItem("valueDates");
    let valueDatesArray;
    try {
        valueDatesArray = JSON.parse(valueDatesString);
        if(!Array.isArray(valueDatesArray)) {
            valueDatesArray = [];
        }
    } catch(e) {
        valueDatesArray = [];
    }
    return valueDatesArray;
}

function checkTodayInValueDates(valueDatesArray) {
    // Get today's date string in the format as 'Thursday, November 09 2023'
    let today = new Date();
    let month = today.toLocaleString('en-us', { month: 'long' });
    let year = today.getFullYear();
    let day = today.getDate().toString().padStart(2, '0');
    let todayString = `${today.toLocaleString('en-US', { weekday: 'long' })}, ${month} ${day} ${year}`;

    // Check if today's date is in the valueDatesArray
    for(let i = 0; i < valueDatesArray.length; i++) {
        if(valueDatesArray[i].valueDate === todayString) {
            console.log("Today's game has already been played.");
            return true;
        }
    }
    console.log("Today's game has not been played yet.")
    return false;
}

function getCountDownToMidnight() {
    let now = new Date();
    let midnight = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
    let differenceInMS = midnight.getTime() - now.getTime();
    // convert it from milliseconds to seconds
    let countdownTime = Math.floor(differenceInMS / 1000);
    return countdownTime
}

function fetchStatistics(valueDatesArray) {
    fetch("/statistics", {
        method : "POST",
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(valueDatesArray),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Network response was not ok ${response.ok}`);
        }
        return response.json();
    })
    .then(data => {
        UpdateUserStatistics(data);
    })
    .catch( error => {
        console.log('There has been a problem with your fetch operation: ', error.message);
    });
}

function prettifyElapsedTime(milliseconds) {
    let seconds = milliseconds / 100
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60, 1);
    return `${mins}min ${secs}s`;
}


function UpdateUserStatistics(statistics) {
    let currentStreak = statistics.current_streak
    let fastest = statistics.fastest
    let maxStreak = statistics.max_streak
    let played = statistics.played

    if (fastest == null) {
        fastest = "-"
    }
    else {
        fastest = prettifyElapsedTime(fastest)
    }

    let playedDiv = document.querySelector("#played")
    playedDiv.textContent = played

    let fastestDiv = document.querySelector("#fastest")
    fastestDiv.textContent = fastest

    let currentStreakDiv = document.querySelector("#current_streak")
    currentStreakDiv.textContent = currentStreak

    let maxStreakDiv = document.querySelector("#max_streak")
    maxStreakDiv.textContent = maxStreak
}



window.onload = function () {
    let valueDatesArray = loadValueDates();
    //  update user statistics
    fetchStatistics(valueDatesArray)

    // check localStore if today's game have been played
    let is_played = checkTodayInValueDates(valueDatesArray);

    let playButton = document.querySelector('#button-play');
    let timerDiv = document.querySelector("#timer-div")
    let countDown = document.querySelector('#countdown');

    // update the div to be displayed
    if (is_played) {    
        // hide play button
        playButton.style.display = 'none';
        // display countdown
        let countdownTime = getCountDownToMidnight()
        timerDiv.style.display = 'block';
        startCountdown(countdownTime, countDown);
    }
    else {
        // display play button
        playButton.style.display = 'block';
        // hide countdown
        timerDiv.style.display = 'none';
    }
};
