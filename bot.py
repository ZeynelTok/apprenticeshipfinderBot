import os
import discord
import json
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from scraper import find_new_apprenticeships
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Scheduler for periodic tasks
scheduler = AsyncIOScheduler()

def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
        
def get_channel_id(server_id):
    config = load_config()
    return config.get(str(server_id))

def get_channel_details(ctx):
    server_id = str(ctx.guild.id)
    channel_id = get_channel_id(server_id)
    
    if not channel_id:
        print(f"No channel configured for server '{ctx.guild.name}'")
        return
    channel = bot.get_channel(int(channel_id))
    if not channel:
        print(f"Channel ID {channel_id} not found in server '{ctx.guild.name}'")
        return
    return channel
    
@bot.command()
@commands.has_permissions(administrator=True)
async def setchannel(ctx, channel: discord.TextChannel):
    server_id = str(ctx.guild.id)
    channel_id = str(channel.id)     
    config = load_config()
    config[server_id] = channel_id
    save_config(config)
    
    await ctx.send(f"Channel set to {channel.mention}")

async def post_new_apprenticeships(channel):
    """Check for new apprenticeships and post them to the Discord channel."""
    new_listings = find_new_apprenticeships()
    if not new_listings:
        await channel.send('No new apprenticeships found right now.')
        return

    for title, company, location, training, salary, posted, expires, full_link in new_listings:
        await channel.send(f"**New Apprenticeship Found:**\n\n**{title} at {company}**\n{location}\n**Qualification:** {training}\n**Annual Wage:** {salary}\n\n**Posted:** {posted}\n**Closes:** {expires}\n{full_link}")


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
   
   
@bot.command(name='hello')
async def hello_command(ctx):
    await ctx.send('Hello!')
    
@bot.command(name='start')
async def start_command(ctx):
    channel = get_channel_details(ctx)
    await ctx.send('Apprenticeship Search Started')
    await post_new_apprenticeships(channel)

@bot.command(name='schedule')
async def schedule_command(ctx):
    if not scheduler.running:
        await ctx.send('Apprenticeship Search Scheduled')
        channel = get_channel_details(ctx)
        scheduler.add_job(post_new_apprenticeships(channel), 'interval', minutes=30)
        scheduler.start()
    else:
        scheduler.shutdown()
        await ctx.send('Apprenticeship Search Stopped')
    
def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        
        
@bot.command(name='status')
async def scheduler_stats(ctx):
    if scheduler.running:
        print("Scheduler is running")
        for job in scheduler.get_jobs():
            next_run_time = job.next_run_time
            await ctx.send(f"Scheduler is running, next run time: {next_run_time}")
    else:
        await ctx.send("Scheduler is not running")
           
# Run the bot
try:
    bot.run(TOKEN)
finally:
    shutdown_scheduler()
