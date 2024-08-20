from typing import Final
import os
from dotenv import load_dotenv
from discord import Intents, Message, app_commands, Interaction
from discord.ext import commands
from responses import get_response
from data_manager import add_student, add_lesson
import webserver

# STEP 0: IMPORT OUR TOKEN FROM SOMEWHERE SAFE
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

# STEP 1: SET UP BOT
intents: Intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

# STEP 2: MESSAGE FUNCTIONALITY
async def send_message(message: Message, user_message: str) -> None:
    if not user_message:
        print("Message was empty, because intents weren't enabled probably")
        return
    
    is_private = user_message[0] == '?'

    if is_private:
        user_message = user_message[1:]
    
    try:
        response: str = get_response(user_message)
        await message.author.send(response) if is_private else await message.channel.send(response)
    except Exception as e:
        print(e) 
    
# STEP 3: HANDLING THE STARTUP FOR THE BOT
@bot.event
async def on_ready() -> None:
    await bot.tree.sync() # register commands with discord
    print(f"{bot.user} is now running!")

# SET UP COMMANDS
@bot.tree.command(name='register', description='Register to the tutoring database!')
@app_commands.describe(first="Your first name", last="Your last name")
async def register(interaction: Interaction, first: str, last: str):

    try:
        await interaction.response.defer() # so the command doesn't time out

        id = add_student(f=first, l=last)
        if id == "Registered":
            await interaction.followup.send("You're already in the database silly...")
        else:
            await interaction.user.send(f"Successfully Registered! Here's your ID for the system: {id}. Make sure to keep it handy!")
            await interaction.followup.send("Please check your DM's for your ID")
    except Exception as e:
        await interaction.followup.send("I made a mistake. Please try again. If this keeps happening alert your tutor.")
        print(e)

    

@bot.tree.command(name='schedule', description='Schedule a tutoring session')
@app_commands.describe(start="Starting time of the session (in military time) HH:MM", end="Ending time of the session (in military time) HH:MM", date="Date of the session YYYY-MM-DD", subject="Subject you want to be tutored in", topic="Topic you would like to learn in your subject", student_id="Your unique ID")
async def schedule(interaction: Interaction, start: str, end: str, date: str, subject: str, topic: str, student_id: str):

    try:
        await interaction.response.defer() # so the command doesn't time out

        res = add_lesson(start=start, end=end, date=date, subject=subject, topic=topic, student_id=student_id)
        if res == -1:
            await interaction.followup.send("That time on that day isn't available, either try a different day or DM your tutor to ask about their schedule!")
        elif res == -2:
            await interaction.followup.send("That is an invalid ID. DM your tutor to either recover your ID or make a new one.")
        elif res == -3:
            await interaction.followup.send("Tutoring isn't available on this day, please try a different day instead!")
        else:
            await interaction.followup.send("Successfully scheduled. Mark your calendar!")
    except Exception as e:
        await interaction.followup.send("I made a mistake. Please try again. If this keeps happening alert your tutor.")
        print(e)

    

# STEP 4: HANDLE THE INCOMING MESSAGES
@bot.event
async def on_message(message: Message) -> None:
    if message.author == bot.user:
        return
    
    username: str = str(message.author)
    user_message: str = message.content
    channel: str = str(message.channel)

    print(f'[{channel}] {username}: "{user_message}"')
    await bot.process_commands(message) # await commands if any

# STEP 5: CREATE MAIN ENTRY POINT
def main() -> None:
    webserver.keep_alive()
    bot.run(TOKEN)

# main()
if __name__ == '__main__':
    main()

# main()
if __name__ == '__main__':
    main()
