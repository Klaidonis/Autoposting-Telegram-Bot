![Header](assets/sova.png)

<p style="font-size: 20px">An autoposting bot is a bot that collects a variety of content from telegram channels, a website, and Instagram and sends it to a closed telegram channel.
In a closed telegram channel, there is an administrator who sees all the content and he puts reactions to the content that he liked, after which this bot sequentially sends photos / videos / text to the open channel.</p>

<h2>1. Goal</h2>
<p style="font-size: 20px">The document describes the functional and non-functional requirements for a telegram bot for automated content creation, defines the boundaries of implementation and the timing of bot development, identifies and determines the risks of implementation.</p>

<h2>Product Boundaries</h2>
<p style="font-size: 20px">Based on the submitted content sources, the bot parses materials into a closed channel with administrators, and if there is a reaction from any of the administrators in the published post, it sends the entry to the main channel with the frequency set in the settings.</p>

<h2>3. Functional requirements</h2>
<table>
    <thead>
    <tr>
        <td style="font-size: 20px">ID Req.</td>
        <td style="font-size: 20px">Requirements</td>
        <td style="font-size: 20px">Description</td>
    </tr>
    </thead>
<tbody>
    <tr>
        <td style="font-size: 20px">FR-001</td>
        <td style="font-size: 20px">The bot must have an admin menu that is accessible to a limited list of people (idtgs are maintained manually)</td>
        <td style="font-size: 20px">called by the /Admin command</td>
    </tr>
    <tr>
        <td style="font-size: 20px">FR-002</td>
        <td style="font-size: 20px">Admin Panel button - Change telegram</td>
        <td style="font-size: 20px">When called, the bot returns the current list of accounts (you can save it to a txt file), the admin edits and sends in response</td>
    </tr>
    <tr>
        <td style="font-size: 20px">FR-003</td>
        <td  style="font-size: 20px">Admin Panel button - Change instagram</td>
        <td style="font-size: 20px">When called, the bot returns the current list of accounts (you can save it to a txt file), the admin edits and sends in response</td>
    </tr>
    <tr>
        <td style="font-size: 20px">FR-004</td>
        <td style="font-size: 20px">Admin Panel button - Change url</td>
        <td style="font-size: 20px">When called, the bot returns the current list of accounts (you can save it to a txt file), the admin edits and sends in response(if the implementation significantly affects the cost of the work, you can exclude it)</td>
    </tr>
    <tr>
        <td style="font-size: 20px">FR-005</td>
        <td style="font-size: 20px">Admin panel button - The period of publication of messages</td>
        <td style="font-size: 20px">The period is set in seconds. After that, the bot takes the next post from the buffer channel with materials (important: it takes only those to which there is at least one reaction) and publishes mainly (sorts posts by publication time from old to new) and saves the date and time of the last post taken from the buffer channel in the database, the following syntactic The analysis is performed from the specified date/time of the following</td>
    </tr>
    <tr>
        <td style="font-size: 20px">FR-006</td>
        <td style="font-size: 20px">Admin Panel button – Analysis period</td>
        <td style="font-size: 20px">The period is specified in seconds. After which the bot goes through the specified sources and collects materials in a buffer channel</td>
    </tr>
</tbody>
</table>
