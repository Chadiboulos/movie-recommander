welcome = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Movieflix API</title>
<style>
  body {
    background: linear-gradient(270deg, #7a7a7a, #ffffff);
    background-size: 400% 400%;
    color: #333;
    font-family: Arial, sans-serif;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 100vh;
    margin: 0;
    animation: Gradient 15s ease infinite;
  }

  .welcome-message {
    opacity: 0;
    font-size: 2em;
    animation: fadeIn 3s forwards;
    margin-bottom: 20px;
  }

  @keyframes fadeIn {
    to {
      opacity: 1;
    }
  }

  @keyframes Gradient {
    0% {
      background-position: 0% 50%;
    }
    50% {
      background-position: 100% 50%;
    }
    100% {
      background-position: 0% 50%;
    }
  }

  .docs-button {
    display: inline-block;
    padding: 10px 20px;
    background-color: #282c34;
    color: #ffffff;
    text-decoration: none;
    border-radius: 5px;
    transition: background-color 0.3s ease;
  }

  .docs-button:hover {
    background-color: #3a3f47;
  }
</style>
</head>
<body>
<div class="welcome-message">Welcome on Movieflix API</div>
<a href="/docs" class="docs-button">Documentation</a>
</body>
</html>
"""
