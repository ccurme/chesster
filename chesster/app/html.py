html_string = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chesster</title>
        <style>
            body {
                background-color: #333333;
                color: #ffffff; /* Text color */
                font-family: 'Courier New', Courier, monospace;
                overflow: hidden;
            }
            #image {
                display: none;   /* Hide image initially */
            }
            /* Add your star related CSS here */
            #star-field {
              width: 100%;
              height: 100%;
              background: #000;
              position: absolute;
              top: 0;
              left: 0;
              z-index: -1;
            }
            .star {
              width: 2px;
              height: 2px;
              position: absolute;
              background: #fff;
              border-radius: 50%;
            }
            .star.far {
              width: 1px;
              height: 1px;
            }
            .star.near {
              width: 4px;
              height: 4px;
            }
            .star.white {
              background: #fff;
              box-shadow: 0 0 15px #fff;
            }
            .star.yellow {
              background: #BFBB40;
              box-shadow: 0 0 15px #BFBB40;
            }
            .star.blue {
              background: #4444ff;
              box-shadow: 0 0 15px #4444ff;
            }
            .star.red {
              background: #ff4444;
              box-shadow: 0 0 15px #ff4444;
            }
        </style>
    </head>
    <body>
        <div id="star-field"></div> <!-- Added star-field div -->
        <div id="content-container" style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh;">
            <h1>Chesster</h1>
            <p id="message">Loading...</p>
            <img id="image" src="" alt="Board will be displayed here"/>
            <ul id='messages'>
        </ul>
        <script>
            /* Add your star related Javascript here */
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

            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onopen = function(event) {
                ws.send("Show me the image");
            };
            ws.onmessage = function(event) {
                var message = document.getElementById('message')
                var image = document.getElementById('image')
                if (event.data.startsWith("Welcome")) {
                    message.innerText = event.data;
                } else if (event.data.startsWith("data:image/svg+xml")) {
                    image.src = event.data
                    image.style.display = 'block';   /* Show image */
                    message.style.display = 'none';  /* Hide message */
                }
            };
        </script>
    </body>
</html>
"""
