/* =========================================================
   TYPINN — TYPING ENGINE
   ========================================================= */

document.addEventListener("DOMContentLoaded", () => {

    /* =====================================================
       DOM ELEMENTS
    ===================================================== */

    const textDisplay = document.getElementById("text-display");
    const typingInput = document.getElementById("typing-input");
    const typingContainer = document.getElementById("typing-container");

    const timeDisplay = document.getElementById("time");
    const wpmDisplay = document.getElementById("wpm");
    const accuracyDisplay = document.getElementById("accuracy");
    const errorsDisplay = document.getElementById("errors");

    const result = document.getElementById("result");
    const finalWpm = document.getElementById("finalWpm");
    const finalAccuracy = document.getElementById("finalAccuracy");
    const finalErrors = document.getElementById("finalErrors");
    const finalCharacters = document.getElementById("finalCharacters");

    const restartButton = document.getElementById("restartBtn");
    const tryAgainButton = document.getElementById("tryAgainBtn");
    const timeButtons = document.querySelectorAll(".time-btn");


    /* =====================================================
       SAFETY CHECK
    ===================================================== */

    if (
        !textDisplay ||
        !typingInput ||
        !typingContainer ||
        !timeDisplay ||
        !wpmDisplay ||
        !accuracyDisplay ||
        !errorsDisplay
    ) {
        console.error("TYPINN: Required typing elements are missing.");
        return;
    }


    /* =====================================================
       PRACTICE TEXT LIBRARY
    ===================================================== */

    const paragraphs = [

        "The quick brown fox jumps over the lazy dog. Learning to type quickly requires patience and consistent practice. Focus on accuracy before trying to increase your speed.",

        "Technology continues to change the way we work and communicate. Good typing skills can help you write faster and spend less time looking at the keyboard.",

        "Practice does not make perfect by itself. Perfect practice makes progress. Take your time, stay relaxed, and focus on every character.",

        "A calm mind helps you maintain a steady typing rhythm. Do not worry about making mistakes. Learn from them and continue moving forward.",

        "Every skill becomes easier when you practice it regularly. Small improvements made every day can eventually become significant progress.",

        "Good typing is not only about speed. Accuracy, rhythm, consistency, and proper finger movement are equally important for becoming a better typist.",

        "The internet has transformed the way people learn, communicate, work, and share information. Digital skills are becoming increasingly valuable in everyday life.",

        "Stay focused on the sentence in front of you instead of thinking about how fast you are typing. A relaxed rhythm often produces better results.",

        "Learning something new can feel difficult at first. With patience and repetition, unfamiliar movements gradually become natural and automatic.",

        "The best way to improve your typing speed is to practice consistently without sacrificing accuracy. Speed will naturally increase as your confidence grows.",

        "Computers allow us to create, communicate, analyze information, and solve problems more efficiently. Strong keyboard skills make many digital tasks easier.",

        "Do not become frustrated when you make a mistake. Mistakes are useful because they show you exactly which characters and movements need more practice.",

        "A steady typing rhythm can help reduce unnecessary pauses. Try to look ahead at the upcoming words while keeping your fingers relaxed on the keyboard.",

        "Consistency is more valuable than short bursts of intense practice. Spending a few minutes typing every day can build a strong long-term habit.",

        "Your typing speed is not fixed. With deliberate practice, better technique, and patience, you can gradually become faster, more accurate, and more comfortable.",

        "Reading regularly can improve your vocabulary and make typing exercises more interesting. Familiar words are easier to recognize and type without hesitation.",

        "The goal of practice is not simply to finish a test. The real goal is to build better habits that continue helping you long after the test is complete.",

        "When you keep your hands relaxed and maintain a comfortable posture, you can type for longer periods without unnecessary tension or fatigue.",

        "Learning to use all of your fingers efficiently may feel strange at first, but proper technique can make typing significantly faster over time.",

        "Progress rarely happens instantly. Keep practicing, measure your results, learn from your mistakes, and give yourself enough time to improve.",

        "A good typist does not need to think about every individual key. With enough practice, common words and letter combinations become automatic.",

        "Focus on accuracy first and speed second. Typing quickly while making many mistakes often creates habits that are difficult to correct later.",

        "Modern work depends heavily on digital communication. Emails, documents, messages, reports, and applications all benefit from efficient typing skills.",

        "Challenge yourself to improve one small part of your typing technique at a time. Gradual improvements can eventually produce impressive results.",

        "The keyboard is a simple tool, but mastering it can save countless hours over the course of a career. Practice today and make tomorrow easier.",

        "When your concentration begins to disappear, slow down slightly and return your attention to the text. Accuracy usually improves when your mind is calm.",

        "Typing tests are useful because they provide measurable feedback. Your WPM, accuracy, errors, and consistency can show how your skills change over time.",

        "Everyone starts somewhere. Do not compare your current typing speed with someone else's best score. Compare today's performance with your own previous results.",

        "Strong typing skills can improve productivity for students, developers, writers, researchers, designers, and almost anyone who works regularly with a computer.",

        "Keep your shoulders relaxed, sit comfortably, and avoid pressing the keys harder than necessary. Efficient movement is one of the foundations of fast typing."

    ];


    /* =====================================================
       STATE
    ===================================================== */

    const state = {

        duration: 15,

        timeLeft: 15,

        timer: null,

        started: false,

        finished: false,

        startTime: null,

        endTime: null,

        currentText: "",

        currentParagraphIndex: -1,

        typedCharacters: 0,

        correctCharacters: 0,

        errors: 0,

        resultSaved: false,

        savingResult: false

    };


    /* =====================================================
       RANDOM TEXT
       Prevent immediate repetition
    ===================================================== */

    function getRandomText() {

        if (paragraphs.length === 1) {
            state.currentParagraphIndex = 0;
            return paragraphs[0];
        }


        let index;

        do {

            index = Math.floor(
                Math.random() * paragraphs.length
            );

        } while (
            index === state.currentParagraphIndex
        );


        state.currentParagraphIndex = index;


        return paragraphs[index]
            .replace(/\s+/g, " ")
            .trim();

    }


    /* =====================================================
       RENDER TEXT
    ===================================================== */

    function renderText() {

        state.currentText = getRandomText();

        textDisplay.innerHTML = "";


        [...state.currentText].forEach((character) => {

            const span = document.createElement("span");

            span.textContent = character;

            textDisplay.appendChild(span);

        });


        setCurrentCharacter(0);

    }


    /* =====================================================
       CURRENT CHARACTER
    ===================================================== */

    function setCurrentCharacter(index) {

        const characters =
            textDisplay.querySelectorAll("span");


        characters.forEach((character) => {

            character.classList.remove("current");

        });


        if (index < characters.length) {

            characters[index].classList.add("current");

        }

    }


    /* =====================================================
       RESET TEST
    ===================================================== */

    function resetTest() {

        stopTimer();


        state.timeLeft =
            state.duration;

        state.started =
            false;

        state.finished =
            false;

        state.startTime =
            null;

        state.endTime =
            null;

        state.typedCharacters =
            0;

        state.correctCharacters =
            0;

        state.errors =
            0;

        state.resultSaved =
            false;

        state.savingResult =
            false;


        timeDisplay.textContent =
            state.duration;

        wpmDisplay.textContent =
            "0";

        accuracyDisplay.textContent =
            "100%";

        errorsDisplay.textContent =
            "0";


        if (result) {

            result.classList.add("hidden");

        }


        typingInput.value =
            "";

        typingInput.disabled =
            false;


        /*
         * Generate a new passage.
         */

        renderText();


        /*
         * Focus the invisible input.
         */

        requestAnimationFrame(() => {

            typingInput.focus();

        });

    }


    /* =====================================================
       START TIMER
    ===================================================== */

    function startTimer() {

        if (
            state.started ||
            state.finished
        ) {
            return;
        }


        state.started =
            true;


        state.startTime =
            performance.now();


        state.endTime =
            state.startTime +
            (state.duration * 1000);


        state.timer =
            setInterval(() => {

                updateTimer();

            }, 100);

    }


    /* =====================================================
       UPDATE TIMER
    ===================================================== */

    function updateTimer() {

        if (
            !state.started ||
            state.finished ||
            !state.endTime
        ) {
            return;
        }


        const remaining =
            Math.max(
                0,
                state.endTime -
                performance.now()
            );


        state.timeLeft =
            Math.ceil(
                remaining / 1000
            );


        timeDisplay.textContent =
            state.timeLeft;


        updateStatistics();


        if (remaining <= 0) {

            state.timeLeft =
                0;

            timeDisplay.textContent =
                "0";

            finishTest();

        }

    }


    /* =====================================================
       STOP TIMER
    ===================================================== */

    function stopTimer() {

        if (state.timer !== null) {

            clearInterval(
                state.timer
            );

            state.timer =
                null;

        }

    }


    /* =====================================================
       CALCULATE TYPING DATA
    ===================================================== */

    function calculateTypingData() {

        const typed =
            typingInput.value;


        let correct = 0;

        let errors = 0;


        const characters =
            textDisplay.querySelectorAll("span");


        characters.forEach(
            (character, index) => {

                character.classList.remove(
                    "correct",
                    "incorrect"
                );


                if (
                    index >=
                    typed.length
                ) {
                    return;
                }


                const expected =
                    character.textContent;

                const actual =
                    typed[index];


                if (
                    actual ===
                    expected
                ) {

                    character.classList.add(
                        "correct"
                    );

                    correct++;

                } else {

                    character.classList.add(
                        "incorrect"
                    );

                    errors++;

                }

            }
        );


        /*
         * Characters typed beyond
         * the passage are errors.
         */

        if (
            typed.length >
            state.currentText.length
        ) {

            errors +=
                typed.length -
                state.currentText.length;

        }


        state.typedCharacters =
            typed.length;

        state.correctCharacters =
            correct;

        state.errors =
            errors;

    }


    /* =====================================================
       HANDLE TYPING
    ===================================================== */

    function handleTyping() {

        if (state.finished) {
            return;
        }


        const typed =
            typingInput.value;


        /*
         * Start timer on first character.
         */

        if (
            !state.started &&
            typed.length > 0
        ) {

            startTimer();

        }


        calculateTypingData();


        setCurrentCharacter(
            Math.min(
                typed.length,
                state.currentText.length
            )
        );


        updateStatistics();


        /*
         * Finish when the entire
         * passage has been typed.
         */

        if (
            typed.length >=
            state.currentText.length
        ) {

            finishTest();

        }

    }


    /* =====================================================
       ELAPSED TIME
    ===================================================== */

    function getElapsedSeconds() {

        if (!state.startTime) {
            return 0;
        }


        const end =
            state.endTime ||
            performance.now();


        return Math.max(
            0.001,
            (
                end -
                state.startTime
            ) / 1000
        );

    }


    /* =====================================================
       CALCULATE WPM
    ===================================================== */

    function calculateWPM() {

        if (
            !state.startTime ||
            state.correctCharacters === 0
        ) {
            return 0;
        }


        const elapsedSeconds =
            getElapsedSeconds();


        const minutes =
            elapsedSeconds / 60;


        const wpm =
            (
                state.correctCharacters /
                5
            ) / minutes;


        return Math.max(
            0,
            Math.round(wpm)
        );

    }


    /* =====================================================
       CALCULATE ACCURACY
    ===================================================== */

    function calculateAccuracy() {

        if (
            state.typedCharacters === 0
        ) {
            return 100;
        }


        return Math.max(
            0,
            Math.min(
                100,
                Math.round(
                    (
                        state.correctCharacters /
                        state.typedCharacters
                    ) * 100
                )
            )
        );

    }


    /* =====================================================
       UPDATE STATISTICS
    ===================================================== */

    function updateStatistics() {

        const wpm =
            calculateWPM();

        const accuracy =
            calculateAccuracy();


        wpmDisplay.textContent =
            Number.isFinite(wpm)
                ? wpm
                : "0";


        accuracyDisplay.textContent =
            `${accuracy}%`;


        errorsDisplay.textContent =
            state.errors;

    }


    /* =====================================================
       FINISH TEST
    ===================================================== */

    function finishTest() {

        if (state.finished) {
            return;
        }


        /*
         * Ignore finish requests
         * before the test starts.
         */

        if (!state.started) {

            return;

        }


        state.finished =
            true;


        stopTimer();


        state.endTime =
            performance.now();


        /*
         * Final calculation.
         */

        calculateTypingData();

        updateStatistics();


        const wpm =
            calculateWPM();

        const accuracy =
            calculateAccuracy();


        /*
         * Final WPM.
         */

        if (finalWpm) {

            finalWpm.textContent =
                wpm;

        }


        /*
         * Final accuracy.
         */

        if (finalAccuracy) {

            finalAccuracy.textContent =
                `${accuracy}%`;

        }


        /*
         * Final errors.
         */

        if (finalErrors) {

            finalErrors.textContent =
                state.errors;

        }


        /*
         * Final characters.
         */

        if (finalCharacters) {

            finalCharacters.textContent =
                state.typedCharacters;

        }


        /*
         * Show result card.
         */

        if (result) {

            result.classList.remove(
                "hidden"
            );

        }


        /*
         * Disable typing.
         */

        typingInput.disabled =
            true;

        typingInput.blur();


        /*
         * Save result.
         */

        saveResult(
            wpm,
            accuracy
        );

    }


    /* =====================================================
       SAVE RESULT
    ===================================================== */

    async function saveResult(
        wpm,
        accuracy
    ) {

        if (
            state.resultSaved ||
            state.savingResult
        ) {
            return;
        }


        state.savingResult =
            true;


        const elapsedSeconds =
            Math.max(
                1,
                Math.round(
                    getElapsedSeconds()
                )
            );


        const data = {

            wpm: wpm,

            accuracy: accuracy,

            errors: state.errors,

            characters:
                state.typedCharacters,

            duration:
                elapsedSeconds,

            language:
                "english"

        };


        try {

            const response =
                await fetch(
                    "/api/save-result",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        credentials:
                            "same-origin",

                        body:
                            JSON.stringify(data)

                    }
                );


            if (!response.ok) {

                throw new Error(
                    `HTTP ${response.status}`
                );

            }


            const serverResult =
                await response.json();


            if (
                !serverResult.success
            ) {

                throw new Error(
                    serverResult.message ||
                    "The server rejected the result."
                );

            }


            state.resultSaved =
                true;


            console.log(
                "TYPINN: Result saved successfully.",
                serverResult
            );


            if (
                Array.isArray(
                    serverResult.achievements
                ) &&
                serverResult.achievements.length > 0
            ) {

                console.log(
                    "TYPINN: New achievements unlocked:",
                    serverResult.achievements
                );

            }

        } catch (error) {

            console.error(
                "TYPINN: Result save failed:",
                error
            );

        } finally {

            state.savingResult =
                false;

        }

    }


    /* =====================================================
       CHANGE TEST DURATION
    ===================================================== */

    function changeDuration(button) {

        const duration =
            Number(
                button.dataset.time
            );


        if (
            !Number.isFinite(duration) ||
            duration <= 0
        ) {
            return;
        }


        timeButtons.forEach(
            (btn) => {

                btn.classList.remove(
                    "active"
                );

            }
        );


        button.classList.add(
            "active"
        );


        state.duration =
            duration;


        resetTest();

    }


    /* =====================================================
       INPUT EVENT
    ===================================================== */

    typingInput.addEventListener(
        "input",
        handleTyping
    );


    /* =====================================================
       PREVENT PASTE
    ===================================================== */

    typingInput.addEventListener(
        "paste",
        (event) => {

            event.preventDefault();

        }
    );


    /* =====================================================
       PREVENT DROP
    ===================================================== */

    typingInput.addEventListener(
        "drop",
        (event) => {

            event.preventDefault();

        }
    );


    /* =====================================================
       TYPING AREA CLICK
    ===================================================== */

    typingContainer.addEventListener(
        "click",
        () => {

            if (
                !state.finished &&
                !typingInput.disabled
            ) {

                typingInput.focus();

            }

        }
    );


    /* =====================================================
       KEYBOARD FOCUS
    ===================================================== */

    document.addEventListener(
        "keydown",
        (event) => {

            if (
                state.finished ||
                typingInput.disabled
            ) {
                return;
            }


            const active =
                document.activeElement;


            const isButton =
                active?.tagName ===
                "BUTTON";

            const isLink =
                active?.tagName ===
                "A";

            const isInput =
                active?.tagName ===
                "INPUT";

            const isTextArea =
                active?.tagName ===
                "TEXTAREA";


            /*
             * Never steal focus from
             * another interactive element.
             */

            if (
                isButton ||
                isLink ||
                isInput ||
                isTextArea
            ) {
                return;
            }


            /*
             * Printable character.
             */

            if (
                event.key.length === 1
            ) {

                typingInput.focus();

            }

        }
    );


    /* =====================================================
       DURATION BUTTONS
    ===================================================== */

    timeButtons.forEach(
        (button) => {

            button.addEventListener(
                "click",
                () => {

                    changeDuration(
                        button
                    );

                }
            );

        }
    );


    /* =====================================================
       RESTART BUTTON
    ===================================================== */

    if (restartButton) {

        restartButton.addEventListener(
            "click",
            resetTest
        );

    }


    /* =====================================================
       TRY AGAIN BUTTON
    ===================================================== */

    if (tryAgainButton) {

        tryAgainButton.addEventListener(
            "click",
            resetTest
        );

    }


    /* =====================================================
       INITIALIZE
    ===================================================== */

    resetTest();


    console.log(
        "TYPINN: Typing engine ready."
    );

});