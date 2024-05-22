import discord
from discord.ext import commands, tasks
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import logging
import asyncio
import os
import concurrent.futures

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Replace with your own values
GUILD_ID = 0000000000000000000      # Server-ID
CHANNEL_ID = 0000000000000000000    # Channel-ID
LINKS_FILE = "monitored_links.txt"  # File to store monitored links

CHROMEDRIVER_PATH = "C:/User/Admin/Desktop/chromedriver.exe"                        # Provide the correct path to chromedriver
CHROME_BINARY_LOCATION = "C:/Program Files/Google/Chrome/Application/chrome.exe"    # Provide the correct path to installed chrome.exe


class LinkMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.check_for_new_offer.start()

    def cog_unload(self):
        self.check_for_new_offer.cancel()
        self.executor.shutdown(wait=False)

    @tasks.loop(minutes=6)
    async def check_for_new_offer(self):
        options = Options()
        options.add_argument('--headless')
        options.binary_location = CHROME_BINARY_LOCATION
        options.executable_path = CHROMEDRIVER_PATH

        guild = self.bot.get_guild(GUILD_ID)
        if guild:
            channel = guild.get_channel(CHANNEL_ID)
            if channel:
                messages = [message async for message in channel.history(limit=100)]  # Limiting to the last 100 messages for efficiency
                sent_links = {msg.content.split('\n')[1] for msg in messages if len(msg.content.split('\n')) > 1}

                monitored_links = self.read_monitored_links()

                for ebay_url in monitored_links:
                    await self.bot.loop.run_in_executor(self.executor, self.process_ebay_url, ebay_url, sent_links, channel, options)

    def process_ebay_url(self, ebay_url, sent_links, channel, options):
        try:
            driver = webdriver.Chrome(options=options)
            driver.get(ebay_url)

            #         v Activate if there is a issue with Cookies v
            #try:
            #    accept_button = driver.find_element(By.XPATH, '//*[@id="gdpr-banner-accept"]')
            #    accept_button.click()
            #except Exception as e:
            #    logger.warning(f"Accept button not found: {e}")

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            offer_elements = soup.select('.aditem')

            for offer_element in offer_elements:
                title_element = offer_element.select_one('h2 a')
                if title_element:
                    offer_link = f'https://www.kleinanzeigen.de{title_element["href"]}'
                    if offer_link not in sent_links:
                        offer_title = title_element.get_text()
                        logger.info(f'Sending new offer: {offer_title} - {offer_link}')
                        asyncio.run_coroutine_threadsafe(channel.send(f'@everyone New offer: {offer_title}\n{offer_link}'), self.bot.loop)
        except Exception as e:
            logger.error(f"Error processing {ebay_url}: {e}")
        finally:
            driver.quit()

    def read_monitored_links(self):
        links = []
        if os.path.exists(LINKS_FILE):
            with open(LINKS_FILE, 'r') as file:
                links = [line.strip() for line in file]
        return links

    def save_monitored_links(self, links):
        with open(LINKS_FILE, 'w') as file:
            for link in links:
                file.write(link + '\n')

    @commands.command()
    async def view(self, ctx):
        monitored_links = self.read_monitored_links()
        if monitored_links:
            links_str = "\n".join(monitored_links)
            await ctx.send(f"Monitored links:\n{links_str}")
        else:
            await ctx.send("No links are currently being monitored.")

    @commands.command()
    async def edit(self, ctx, *links):
        if not links:
            await ctx.send("Please provide at least one link to edit or change.")
            return

        self.save_monitored_links(links)
        await ctx.send("Monitored links have been updated.")

async def setup(bot):
    await bot.add_cog(LinkMonitor(bot))
