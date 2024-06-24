
# Materials Master

Materials Master is a Discord bot designed to help crafters place orders for gatherers to fulfill in the game Pax Dei. This bot streamlines the requisition process by allowing users to request materials, track progress, provide feedback, and manage archived jobs efficiently.

## Table of Contents

1. [Features](#features)
2. [Getting Started](#getting-started)
3. [Commands](#commands)
4. [Upcoming Features](#upcoming-features)
5. [Contributing](#contributing)
6. [License](#license)

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
