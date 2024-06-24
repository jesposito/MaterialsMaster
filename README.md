# Materials Master (MatMaster) Requisition Bot

Welcome to Materials Master (MatMaster), a Discord bot designed to facilitate teamwork in resource gathering for games like Pax Dei. MatMaster helps players create and manage requisitions for materials, making it easier to collaborate and fulfill resource requests efficiently.

## Features

### 1. Requisition Management
MatMaster allows users to create, manage, and track requisitions for materials. Requisitions include details such as material type, quantity, payment method, deadline, and region.

### 2. Interactive Commands
Users can interact with MatMaster through simple commands. The bot provides guidance for creating and updating requisitions, ensuring a smooth user experience.

### 3. Channel Configuration
Server administrators can configure requisition and archive channels for managing and storing completed requisitions. The bot also requires the server name to distinguish between different servers.

### 4. Reaction-Based Workflow
MatMaster uses Discord reactions to manage the workflow of requisitions. Users can accept jobs by reacting with ✋ and mark them as completed with ✅.

### 5. Feedback Collection
After a requisition is completed, MatMaster collects feedback from the requester to improve the process and provide insights for future collaborations.

### 6. Donation Support
Users can support the development of MatMaster by donating through a provided link. The donation link is occasionally included in archived requisition posts.

## Commands

### Help Command
- **`!mm_help`**: Displays a help message with an overview of all commands.

### Configuration Command
- **`!mm_config <requisitions_channel_id> <archive_channel_id> <server_name>`**: Configures the channels for managing requisitions and sets the server name. This command is restricted to users with administrator permissions.

### Requisition Commands
- **`!mm_request [material, quantity, payment, deadline, region]`**: Starts a new requisition. Users can either provide all details at once or be guided through the process interactively.
- **`!mm_update_request <message_id>, <new_quantity>, <new_payment>, <new_deadline>`**: Updates an existing requisition. Users can provide the details at once or be guided through the update process interactively.

## Usage Workflow

1. **Adding the Bot**: When MatMaster is added to a server, it sends a welcome message prompting the administrators to configure the requisitions and archive channels using the `!mm_config` command.

2. **Creating a Requisition**:
   - A user types `!mm_request` in a text channel.
   - The bot prompts for the material, quantity, payment method, deadline, and region if not provided as a single input.
   - The bot validates the input and creates a requisition if valid, posting it in the configured requisitions channel with reactions for accepting and completing the job.

3. **Accepting and Completing Jobs**:
   - Users can accept the job by reacting with ✋ and mark it as completed with ✅.
   - Once all parties have completed the requisition, the requester confirms completion with a ✅ reaction.
   - The requisition is moved to the archive channel.

4. **Collecting Feedback**:
   - After moving the requisition to the archive channel, the bot asks the requester for feedback, which is appended to the archived message.

## Example Use Case

In games like Pax Dei, where players need to gather resources collaboratively, MatMaster helps coordinate efforts by:
- Allowing players to request materials and specify the quantity, payment, deadline, and region.
- Enabling other players to accept and complete these requests efficiently.
- Storing completed requests in an archive for future reference and feedback.

## Support the Bot

If you find MatMaster helpful, please consider donating to support its development: [Ko-fi Donation Link](https://ko-fi.com/jedespo).

## Conclusion

MatMaster is a versatile and user-friendly bot that enhances teamwork and resource management in gaming communities. By providing a structured and interactive way to handle requisitions, it ensures players can focus on what they do best—playing the game and collaborating with their teammates. Enjoy using MatMaster and happy gathering!
