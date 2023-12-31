var starsInterval = null;
(function () {
    var starFieldWidth = window.innerWidth;
    var starFieldHeight = window.innerHeight;
    addStars(starFieldWidth, starFieldHeight, 50);
    animateStars(starFieldWidth, 2);
})();

window.addEventListener('resize', function() {
    var starFieldWidth = window.innerWidth;
    var starFieldHeight = window.innerHeight;

    // Remove old stars
    var starField = document.getElementById('star-field');
    while (starField.firstChild) {
        starField.firstChild.remove();
    }

    // Add new stars
    addStars(starFieldWidth, starFieldHeight, 50);
    animateStars(starFieldWidth, 2);
});

function addStars(starFieldWidth, starFieldHeight, noOfStars) {
    var starField = document.getElementById('star-field');
    var numberOfStars = noOfStars;
    for (var i = 0; i < numberOfStars; i++) {
      var star = document.createElement('div');
      star.className = 'star';
      var topOffset = Math.floor((Math.random() * starFieldHeight) + 1);
      var leftOffset = Math.floor((Math.random() * starFieldWidth) + 1);
      star.style.top = topOffset + 'px';
      star.style.left = leftOffset + 'px';
      star.style.position = 'absolute';
      starField.appendChild(star);
    }
}

function animateStars(starFieldWidth, speed) {
    var starField = document.getElementById('star-field');
    var stars = starField.childNodes;

    function getStarColor(index) {
        if (index % 8 == 0)
        return 'red';
        else if (index % 10 == 0)
        return 'yellow';
        else if (index % 17 == 0)
        return 'blue';
        else
        return 'white';
    }

    function getStarDistance(index) {
        if (index % 6 == 0)
        return '';
        else if (index % 9 == 0)
        return 'near';
        else if (index % 2 == 0)
        return 'far';
        else
        return 0;
    }

    function getStarRelativeSpeed(index) {
        if (index % 6 == 0)
        return 1;
        else if (index % 9 == 0)
        return 2;
        else if (index % 2 == 0)
        return -1;
        else
        return 0;
    }
    // Clear the previous interval
    if (starsInterval) {
        clearInterval(starsInterval);
    }

    starsInterval = setInterval(function() {
        for (var i = 1; i < stars.length; i++) {
        stars[i].className = 'star' + ' ' + getStarColor(i) + ' ' + getStarDistance(i);

        var currentLeft = parseInt(stars[i].style.left, 10);
        var leftChangeAmount = speed + getStarRelativeSpeed(i);
        var leftDiff;
        if (currentLeft - leftChangeAmount < 0) {
            leftDiff = currentLeft - leftChangeAmount + starFieldWidth;
        }
        else {
            leftDiff = currentLeft - leftChangeAmount;
        }
        stars[i].style.left = (leftDiff) + 'px';
        }
    }, 20);
}

var chatForm = document.getElementById('chat-form');
var chatInput = document.getElementById('chat-input');
var chatMessages = document.getElementById('chat-messages');

chatForm.addEventListener('submit', function(event) {
    event.preventDefault();
    var message = chatInput.value;
    chatInput.value = '';
    if (message) {
        ws.send(message);
    }
});

function updateMessageOpacity() {
    var chatContainer = document.getElementById('chat-container');
    var chatMessages = document.getElementById('chat-messages');
    var messages = chatMessages.querySelectorAll('li');
    var containerHeight = chatContainer.offsetHeight;

    for (var i = 0; i < messages.length; i++) {
        var message = messages[i];
        var messagePos = message.offsetTop - chatContainer.scrollTop;
        var fadeStartPoint = 0.15 * containerHeight;
        var opacity = 1;
        if (messagePos < fadeStartPoint) {
            opacity = (messagePos / fadeStartPoint);
            opacity = Math.min(1, Math.max(0, opacity));
        }
        message.style.opacity = opacity;
        message.classList.add('transparent');
    }
}


var ws = new WebSocket("ws://localhost:8000/ws");
ws.onopen = function(event) {
    ws.send("Show me the image");
};
ws.onmessage = function(event) {
    var message = document.getElementById('message')
    var image = document.getElementById('image')
    if (event.data.startsWith("Welcome")) {  /* TODO: fix this hack */
        message.innerText = event.data;
    } else if (event.data.startsWith("data:image/svg+xml")) {
        image.src = event.data
        image.style.display = 'block';   /* Show image */
        message.style.display = 'none';  /* Hide message */
    } else {
        var li = document.createElement('li');
        li.innerText = event.data;
        // Determine if the message is even or odd and add the appropriate class
        li.className = chatMessages.childNodes.length % 2 == 0 ? 'message-white' : 'message-teal';
        chatMessages.insertBefore(li, chatMessages.firstChild); // Insert new message at the top
    }
    updateMessageOpacity();
};
document.getElementById('chat-container').addEventListener('scroll', updateMessageOpacity);
