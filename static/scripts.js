var attemptCounts = {};

function showToast(message) {
    var container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed top-4 left-1/2 z-50 -translate-x-1/2';
        document.body.appendChild(container);
    }
    var toast = document.createElement('div');
    toast.className = 'rounded-xl border border-rule bg-white px-5 py-3 font-sans text-sm text-ink shadow-paper opacity-0 transition-opacity duration-200';
    toast.textContent = message;
    container.appendChild(toast);
    requestAnimationFrame(function() { toast.style.opacity = '1'; });
    setTimeout(function() {
        toast.style.opacity = '0';
        setTimeout(function() { toast.remove(); }, 200);
    }, 2000);
}

function getRemainingLetters(exclude) {
    var pool = '';
    document.querySelectorAll('.input-letter-cue').forEach(function(t) {
        if (t.value) pool += t.value.toUpperCase();
    });
    document.querySelectorAll('.input-letter-solution').forEach(function(t) {
        if (t === exclude) return;
        if (t.value) {
            pool = pool.replace(t.value.toUpperCase(), '');
        }
    });
    return pool;
}

function handleInput(element, allowedChars = null) {
    element.value = element.value.toUpperCase();
    var rejected = false;
    if (allowedChars !== null && !allowedChars.includes(element.value)) {
        showToast('Not in this jumble — pick from ' + allowedChars);
        element.value = '';
        rejected = true;
    }
    if (!rejected && element.value !== '' && element.classList.contains('input-letter-solution')) {
        var remaining = getRemainingLetters(element);
        if (!remaining.includes(element.value)) {
            showToast('Not available — remaining letters: ' + (remaining || 'none'));
            element.value = '';
            rejected = true;
        }
    }

    var group = element.closest('.jumble-group[data-jumble-index]');

    var container = group || element.closest('.word-group');

    if (element.value != '' && !rejected) {
        if (container) {
            var tiles = Array.from(container.querySelectorAll('input.tile'));
            var idx = tiles.indexOf(element);
            if (idx >= 0 && idx < tiles.length - 1) {
                tiles[idx + 1].focus();
            }
        }
        if (group) {
            var allTiles = group.querySelectorAll('input[name="jumble_letters"]');
            var allFilled = Array.from(allTiles).every(function(t) { return t.value !== ''; });
            if (allFilled) {
                autoValidateJumble(group.dataset.jumbleIndex);
            }
        }
    } else if (group) {
        clearSingleJumbleFeedback(group.dataset.jumbleIndex);
    }
}

function handleBackspace(e) {
    var el = e.target;
    if (!el || !el.classList.contains('tile')) return;

    var group = el.closest('.jumble-group[data-jumble-index]') ||
                el.closest('.word-group');
    if (!group) return;

    var tiles = Array.from(group.querySelectorAll('input.tile'));
    var idx = tiles.indexOf(el);

    if (el.value !== '') {
        el.value = '';
        el.dispatchEvent(new Event('input', { bubbles: true }));
        e.preventDefault();
    } else if (idx > 0) {
        var prev = tiles[idx - 1];
        prev.focus();
        prev.value = '';
        prev.dispatchEvent(new Event('input', { bubbles: true }));
        e.preventDefault();
    }
}

document.addEventListener('beforeinput', function(e) {
    if (e.inputType === 'deleteContentBackward') handleBackspace(e);
});
document.addEventListener('keydown', function(e) {
    if (e.key === 'Backspace') handleBackspace(e);
});

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

function clearSingleJumbleFeedback(idx) {
    var card = document.querySelector('.jumble-group[data-jumble-index="' + idx + '"]');
    if (!card) return;
    card.classList.remove('is-correct', 'is-wrong');
    var badge = card.querySelector('.jumble-badge');
    if (badge) badge.remove();
}

function clearJumbleFeedback() {
    document.querySelectorAll('.jumble-group[data-jumble-index]').forEach(card => {
        card.classList.remove('is-correct', 'is-wrong');
        const badge = card.querySelector('.jumble-badge');
        if (badge) badge.remove();
    });
}

function autoValidateJumble(jumbleIndex) {
    attemptCounts[jumbleIndex] = (attemptCounts[jumbleIndex] || 0) + 1;
    var form = document.getElementById('form');
    fetch(form.action, {
        method: "POST",
        body: new FormData(form),
    })
    .then(response => response.json())
    .then(data => {
        clearSingleJumbleFeedback(jumbleIndex);
        var result = {};
        result[jumbleIndex] = data.is_jumbles_correct[jumbleIndex];
        applyJumbleFeedback(result);
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

function shortDate(valueDate) {
    var datePart = valueDate.split(', ')[1];
    if (!datePart) return valueDate;
    var tokens = datePart.split(' ');
    return tokens[0] + ' ' + parseInt(tokens[1]);
}

function buildShareText(valueDate, elapsedMs) {
    var time = formatElapsed(elapsedMs);
    var jumbleCount = document.querySelectorAll('.jumble-group[data-jumble-index]').length;
    var parts = [];
    for (var i = 1; i <= jumbleCount; i++) {
        var count = attemptCounts[String(i)] || 1;
        parts.push(i + ' ' + '●'.repeat(count));
    }
    var solCount = attemptCounts['solution'] || 1;
    return 'Pastiche 🧩 ' + shortDate(valueDate) + ' · ' + time + '\n' +
           parts.join(' · ') + '\n' +
           '🎯 ' + '●'.repeat(solCount);
}

function copyShareText() {
    var text = document.getElementById('share-text').textContent;
    navigator.clipboard.writeText(text).then(function() {
        showToast('Copied to clipboard!');
    });
}

function showSolvedCard(valueDate, elapsedMs) {
    var shareText = buildShareText(valueDate, elapsedMs);
    var resultsEl = document.getElementById('results');
    resultsEl.innerHTML =
        '<div class="mx-auto mt-2 max-w-sm rounded-2xl border border-rule bg-white/70 p-6 shadow-paper">' +
            '<p class="font-display text-xl font-semibold tracking-tight text-ink">Solved.</p>' +
            '<p class="mt-1 font-display text-sm tracking-[0.18em] text-muted">' + formatElapsed(elapsedMs) + '</p>' +
            '<pre id="share-text" class="mt-4 rounded-xl bg-paper px-4 py-3 text-left font-sans text-sm leading-relaxed text-ink">' +
                shareText.replace(/</g, '&lt;') +
            '</pre>' +
            '<div class="mt-4 flex items-center justify-center gap-3">' +
                '<button onclick="copyShareText()" class="rounded-full bg-accent px-5 py-2.5 font-display text-sm font-semibold tracking-tight text-white shadow-paper transition hover:brightness-110 active:translate-y-px">' +
                    'Copy to share' +
                '</button>' +
                '<a href="/" class="font-display text-sm font-semibold text-muted underline decoration-rule underline-offset-4 transition hover:text-ink">' +
                    'Back to home' +
                '</a>' +
            '</div>' +
        '</div>';
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
    setTimeout(() => { showSolvedCard(valueDate, elapsedTime); }, cascadeDoneMs);
}

function handleFormSubmit(form) {
    event.preventDefault();
    attemptCounts['solution'] = (attemptCounts['solution'] || 0) + 1;
    fetch(form.action, {
        method : "POST",
        body: new FormData(form),
    })
    .then(response => response.json())
    .then(data => {
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