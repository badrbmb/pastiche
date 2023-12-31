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
        // update div with id="results"
        let output = "";
        if (data.is_correct) {
            output += '<p style="color:green; text-align: center;">Well done ※\(^o^)/※</p>'
            output += '<p style="color:green; text-align: center;">Redirecting you to home ...</p>'
            output += '<div class="success-container"><dotlottie-player src="https://lottie.host/7684ce67-b168-401d-9730-9ff6d578b2cc/Nd5PLkFxzr.json" background="#00000000" speed="1" style="width: 800px; height: 800px" direction="1" mode="normal" autoplay></dotlottie-player></div>'
            // store results in localStore for statistics
            let valueDate = form.elements.value_date.value;
            // compute the elasped time
            let elapsedTime = computeElapsedTime()
            storeValueDate(valueDate, elapsedTime);
            // redirect to home page after 3 seconds
            setTimeout(function() {
                window.location.href = "/";
            }, 3500);
        }
        else {
            // check each individial jumble
            for (var key in data.is_jumbles_correct) {
                var isCorrect = data.is_jumbles_correct[key]
                if (isCorrect) {
                    output += '<p style="color:green; text-align: center;">Jumble #'+ key +' is correct ※\(^o^)/※ </p>';
                }
                else {
                    output += '<p style="color:red; text-align: center;">Jumble #'+ key +' is wrong •͡˘㇁•͡˘ \nKeep trying! </p>';
                }
                
            }
        }
        document.getElementById('results').innerHTML = output;
    });
}