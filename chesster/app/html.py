html_string = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chesster</title>
        <style>
            #image {
                display: none;   /* Hide image initially */
            }
        </style>
    </head>
    <body>
        <h1>Chesster</h1>
        <p id="message">Loading...</p>
        <img id="image" src="" alt="Board will be displayed here"/>
        <ul id='messages'>
        </ul>
        <script>
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