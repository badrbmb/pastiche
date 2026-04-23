function handleInput(element, allowedChars = null) {
    element.value = element.value.toUpperCase();
    if (allowedChars !== null && !allowedChars.includes(element.value)) {
        alert('Sorry, `' + element.value + '` is not a valid option ¯\_(ツ)_/¯. \nPlease pick one letter from `' + allowedChars + '`');
        element.value = '';
    }
    if (element.value != '') {
        var inputs = document.getElementsByTagName("input");
        var currentIndex = Array.from(inputs).indexOf(element);
        var nextIndex = currentIndex + 1;
        var nextInput = inputs[nextIndex];
        if (nextInput) {
        nextInput.focus();
        }
    }
}

window.onload = function() {
    let currentTime = new Date().getTime();
    localStorage.setItem('startTime', currentTime);
}
  

// function to update the available letters to be used for the solution
$(document).ready(function () {
    // get all input letters counting towards the solution
    function getAvailableLetters() {
        var availableLetters = "";
        $.each($(".input-letter-cue"), function() {
            var value = $(this).val();
            if (value) {
                availableLetters += value.toUpperCase();
            }
        });
        return availableLetters;
    }

    function getUsedLetters() {
        var usedLetters = '';
        $(".input-letter-solution").each(function() {
            usedLetters += $(this).val();
        });
        return usedLetters;
    }

    function getDisplayLetters() {
        var availableLetters = getAvailableLetters();
        var usedLetters = getUsedLetters();
        var displayLetters = availableLetters
        // Remove solution letters from availableLetters
        for (var i = 0; i < usedLetters.length; i++) {
            displayLetters = displayLetters.replace(usedLetters.charAt(i).toUpperCase(), '');
        }
        return displayLetters;
    }

    // set the available letters based on the inputs
    $(".input-letter-cue").on('input', function () {
        var letters = getDisplayLetters();
        $(".available-letters").text(letters);
    });

    // set the available letters based on the used inputs in the solution
    $("[name=solution_letters]").on('input', function () {
        var letters = getDisplayLetters();
        $(".available-letters").text(letters);
    });
});

function storeValueDate(valueDate, elapsedTime) {
    // Initialize valueDatesArray as Array
    let valueDatesArray;
    let valueDatesString = localStorage.getItem("valueDates")
    try {
        valueDatesArray = JSON.parse(valueDatesString);
        if (!Array.isArray(valueDatesArray)) {
            valueDatesArray = [];
        }
    } catch (e) {
        valueDatesArray = [];
    }
    // add new object {valueDate, elapsedTime} to the array
    valueDatesArray.push({ valueDate, elapsedTime });
    // store the updated array back to localStorage
    localStorage.setItem("valueDates", JSON.stringify(valueDatesArray));
    console.log(valueDatesArray)
}


function computeElapsedTime() {
    let loadTime = Number(localStorage.getItem("startTime"));
    let currentTime = new Date().getTime();
    let elapsedTime = currentTime - loadTime;
    return elapsedTime;
}

function clearJumbleFeedback() {
    document.querySelectorAll('.jumble-group[data-jumble-index]').forEach(card => {
        card.classList.remove('is-correct', 'is-wrong');
        const badge = card.querySelector('.jumble-badge');
        if (badge) badge.remove();
    });
}

function applyJumbleFeedback(isJumblesCorrect) {
    Object.keys(isJumblesCorrect).forEach(idx => {
        const card = document.querySelector('.jumble-group[data-jumble-index="' + idx + '"]');
        if (!card) return;
        const correct = isJumblesCorrect[idx];
        const stateClass = correct ? 'is-correct' : 'is-wrong';
        card.classList.add(stateClass);
        const badge = document.createElement('span');
        badge.className = 'jumble-badge ' + stateClass;
        badge.setAttribute('aria-label', correct ? 'correct' : 'try again');
        badge.textContent = correct ? '✓' : '✗';
        card.appendChild(badge);
    });
}

function summariseProgress(isJumblesCorrect) {
    const values = Object.values(isJumblesCorrect);
    const nCorrect = values.filter(Boolean).length;
    const nTotal = values.length;
    if (nCorrect === nTotal) return 'All jumbles match — now arrange the answer below';
    if (nCorrect === 0)      return 'Keep going — none match yet';
    return nCorrect + ' of ' + nTotal + ' correct — keep going';
}

function formatElapsed(ms) {
    const total = Math.max(0, Math.floor(ms / 1000));
    const mm = String(Math.floor(total / 60)).padStart(2, '0');
    const ss = String(total % 60).padStart(2, '0');
    return mm + ':' + ss;
}

function triggerSolvedAnimation(valueDate) {
    const tiles = document.querySelectorAll('input.input-letter-solution');
    const STAGGER_MS = 80;
    const FLIP_MS = 520;
    tiles.forEach((tile, i) => {
        tile.style.animationDelay = (i * STAGGER_MS) + 'ms';
        tile.classList.add('tile-win');
    });
    const elapsedTime = computeElapsedTime();
    storeValueDate(valueDate, elapsedTime);

    const cascadeDoneMs = (tiles.length ? (tiles.length - 1) * STAGGER_MS : 0) + FLIP_MS;
    setTimeout(() => {
        document.getElementById('results').innerHTML =
            '<p class="font-display text-xl font-semibold tracking-tight text-ink">Solved.</p>' +
            '<p class="mt-1 font-display text-sm tracking-[0.18em] text-muted">' + formatElapsed(elapsedTime) + '</p>';
    }, cascadeDoneMs);
    setTimeout(() => { window.location.href = "/"; }, cascadeDoneMs + 1500);
}

function handleFormSubmit(form) {
    // stop form from submitting normally
    event.preventDefault();
    // use Fetch API to submit form
    fetch(form.action, {
        method : "POST",
        body: new FormData(form),
    })
    .then(response => response.json())
    .then(data => {
        // reset any prior per-jumble state and reapply based on this submission
        clearJumbleFeedback();
        applyJumbleFeedback(data.is_jumbles_correct);

        if (data.is_correct) {
            triggerSolvedAnimation(form.elements.value_date.value);
            return;
        }
        document.getElementById('results').innerHTML =
            '<p class="font-display text-sm text-muted">' + summariseProgress(data.is_jumbles_correct) + '</p>';
    });
}