# Materials Master (MatMaster) Requisition Bot

MatMaster is a Discord bot designed to streamline material requisitions within a Discord server. It allows users to request materials, update requests, and provide feedback upon completion. The bot uses PostgreSQL for persistent storage, ensuring that data is not lost between restarts.

## Features

- **Request Materials**: Users can create material requisitions by specifying the material, quantity, payment method, and deadline.
- **Update Requests**: Users can update existing requisitions with new details.
- **Feedback Collection**: After a requisition is completed and archived, the bot sends a direct message to the requester to collect feedback.
- **Persistent Storage**: Uses PostgreSQL to store requisitions and channel configurations, ensuring data is retained across bot restarts.

## Pending Features

- **Notification System**: Implementing notifications for pending requisitions close to their deadlines.
- **Admin Commands**: Adding administrative commands for better management of requisitions and channels.
- **Web Dashboard**: Developing a web dashboard for visualizing and managing requisitions.
- **Enhanced Validation**: Improving validation for user inputs to ensure data integrity.

## Setup and Deployment

### Prerequisites

- [Python 3.8+](https://www.python.org/downloads/)
- [Discord Bot Token](https://discord.com/developers/applications)
- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
- [PostgreSQL Database](https://www.heroku.com/postgres)

### Local Setup

1. **Clone the Repository**

    ```sh
    git clone https://github.com/your-username/materials-master.git
    cd materials-master
    ```

2. **Create a Virtual Environment and Install Dependencies**

    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3. **Set Environment Variables**

    Create a `.env` file and add your environment variables:

    ```env
    DISCORD_TOKEN=your_discord_token
    DATABASE_URL=your_postgresql_database_url
    ```

4. **Run the Bot Locally**

    ```sh
    python matmaster.py
    ```

## Commands

- **!mm_help**: Displays the help message.
- **!mm_set_channels <requisitions_channel_id> <archive_channel_id>**: Sets up the channels for managing requisitions and archiving them once completed.
- **!mm_request [material, quantity, payment, deadline]**: Starts a new requisition. You can enter all details at once or follow the interactive prompts.
- **!mm_update_request <message_id>, <new_quantity>, <new_payment>, <new_deadline>**: Updates an existing requisition.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
