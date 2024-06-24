
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
- **Progress Tracking**: Update the progress of requisitions.
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

- `!mm_update_request <message_id> [new_quantity] [new_payment] [new_deadline]`
  - Update an existing requisition.
  - Example: `!mm_update_request 123456789012345678 60 20 Gold Bars 2024-07-31`

- `!mm_progress <message_id> <percentage>`
  - Update the progress of a requisition.
  - Example: `!mm_progress 123456789012345678 50`

- `!mm_feedback <message_id> <feedback>`
  - Provide feedback for a completed requisition.
  - Example: `!mm_feedback 123456789012345678 The materials were delivered on time and in good condition.`

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
   ```

2. **Create a `.env` File**:
   - Create a file named `.env` in the root of your project.
   - Add your Discord token to this file:
     ```env
     DISCORD_TOKEN=your_discord_token_here
     ```

3. **Modify Your Code to Load the `.env` File**:
   - In your `matmaster.py`, add the following at the top of the file:
     ```python
     from dotenv import load_dotenv
     load_dotenv()
     ```

By following these steps, you ensure that your Discord token is securely stored and not hardcoded in your files.

## Upcoming Features

- **Persistence**: Save requisition data to a database for persistent storage.
- **Improved Reminders**: Enhance reminder functionality with more flexible scheduling options.
- **Archived Job Details**: Include details on who fulfilled the order and feedback in the archived post.
- **Companion Site**: Create a website where orders can be looked up and managed.
- **Donation Function**: Add a feature for users to donate and support the development.
- **Server and Area Information**: Include server and area details in posts and make them filterable.

## Contributing

We welcome contributions to enhance the functionality of Materials Master. To contribute, follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes and commit them (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a pull request.

Please make sure to update tests as appropriate.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

Feel free to reach out for any support or questions regarding the setup and usage of Materials Master. Happy crafting!
