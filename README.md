# Materials Master

Materials Master is a Discord bot designed to help crafters place orders for gatherers to fulfill in the game Pax Dei. This bot streamlines the requisition process by allowing users to request materials, track progress, provide feedback, and manage archived jobs efficiently.

## Table of Contents

1. [Features](#features)
2. [Getting Started](#getting-started)
3. [Commands](#commands)
4. [Storing the Discord Token](#storing-the-discord-token)
5. [Upcoming Features](#upcoming-features)
6. [Contributing](#contributing)
7. [License](#license)

## Features

- **Requisition Management**: Create, update, and track material requests.
- **Feedback Collection**: Collect and archive feedback from requesters.
- **Channel Setup**: Set channels for requisitions and archives.
- **Reminders**: Automatic reminders for open requisitions.

## Getting Started

### Prerequisites

- Python 3.9.12
- Discord bot token
- Required Python packages (see `requirements.txt`)

### Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/materials-master.git
    cd materials-master
    ```

2. Create and activate a virtual environment:
    ```sh
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. Install dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. Set up environment variables in a `.env` file:
    ```env
    DISCORD_TOKEN=your_discord_token_here
    ```

5. Run the bot:
    ```sh
    python matmaster.py
    ```

## Commands

### General Commands

- `!mm_help`
  - Displays the help message with all available commands.

### Requisition Commands

- `!mm_set_channels <requisitions_channel_id> <archive_channel_id>`
  - Set the channel IDs for requisitions and archives.
  - Example: `!mm_set_channels 123456789012345678 987654321098765432`

- `!mm_request [material, quantity, payment, deadline]`
  - Create a new requisition.
  - Example: `!mm_request Iron, 50, 10 Gold Bars, 2024-06-30`
  - Alternatively, simply type `!mm_request` and the bot will guide you through the process interactively.

- `!mm_update_request <message_id>, <new_quantity>, <new_payment>, <new_deadline>`
  - Update an existing requisition.
  - Example: `!mm_update_request 123456789012345678, 60, 20 Gold Bars, 2024-07-31`
  - Alternatively, simply type `!mm_update_request` and the bot will guide you through the update process interactively.

### Feedback

- Once your requisition is completed and archived, you will receive a direct message to provide feedback. This helps us improve the process based on your experience.

## Storing the Discord Token

### Using Environment Variables on Heroku

If you are deploying your bot on Heroku, you can store the Discord token as an environment variable:

1. **Go to Your Heroku Dashboard**:
   - Select your application.
   - Go to the "Settings" tab.
   - Click "Reveal Config Vars".

2. **Add the Discord Token**:
   - Add a new variable with the key `DISCORD_TOKEN` and the value as your actual token.

### Using a `.env` File Locally

If you are running the bot locally, you can store the Discord token in a `.env` file. You will need to make sure you have the `python-dotenv` package installed to load the variables from this file.

1. **Install `python-dotenv`**:
   ```sh
   pip install python-dotenv
