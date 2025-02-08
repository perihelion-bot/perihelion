import PIL.Image
import discord
from discord import app_commands
from discord.ext import commands
from utils.logging import log
from utils.embeds import *
from typing import Optional
from utils.translation import JSONTranslator
from utils.data import get_data_manager
from discord.app_commands import locale_str

from PIL import Image, ImageDraw, ImageFont
from utils.image import get_wrapped_text, crop_circle
from random import gauss, choice
from math import floor, log10
from io import BytesIO

class DistanceCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.translator: JSONTranslator = client.tree.translator


    @commands.Cog.listener()
    async def on_ready(self):
        log.info("Cog: distance loaded")

    objects = {
        4: {
            "asset": "assets/distance/perihelion.png"
        },
        5.91*10**7: {
            "asset": "assets/distance/mercury.png"
        },
        1.08*10**8: {
            "asset": "assets/distance/venus.png"
        },
        1.495*10**8: {
            "asset": "assets/distance/earth.png"
        },
        2.29*10**8: {
            "asset": "assets/distance/mars.png"
        },
        7.8*10**8: {
            "asset": "assets/distance/jupiter.png"
        },
        1.43*10**9: {
            "asset": "assets/distance/saturn.png"
        },
        2.88*10**9: {
            "asset": "assets/distance/uranus.png"
        },
        4.5*10**9: {
            "asset": "assets/distance/neptune.png"
        }
    }

    @app_commands.command(name="command_distance", description="command_distance")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def distance(self, interaction: discord.Interaction):
        distance = floor(10**gauss(mu=8,sigma=3))-10
        comment = ""
        if distance <= 0:
            distance = 0
            comment = "You are *in* the Sun. Surprisingly better than the corona, though."
        elif distance <= 5:
            comment = "Perihelion."
        elif distance < 10**6.5:
            comment = choice([f"You're in the corona, in the millions of degrees. {choice(["Ought to get an ice pack.",
                                                                                           "Might want to bring a fan.",
                                                                                           "You should really get some refreshments."])}",
                              "This is a really good view of the Sun. Too bright though, 1 star."])
        elif distance < 5.9*10**7:
            comment = "Closer than Mercury."
        elif distance < 5.92*10**7:
            comment = "You're in Mercury's orbit; hope you don't crash!"
        elif distance < 1.07*10**8:
            comment = "Between the two hottest planets."
        elif distance < 1.09*10**8:
            comment = "In Venus' orbit. You should get used to the taste of SO₂."
        elif distance < 1.49*10**8:
            comment = "Between the twin planets, Venus and Earth."
        elif distance < 1.5*10**8:
            comment = "YOU'RE ABOUT TO HIT EARTH OH NO IT'S SO OVER"
        elif distance < 2.28*10**8:
            comment = "In the space every sci-fi fan wants to traverse; the midst of Earth and Mars."
        elif distance < 2.3*10**8:
            comment = "You should recharge the rovers while you're on Mars."
        elif distance < 3.08*10**8:
            comment = "Approaching the Asteroid Belt..."
        elif distance < 4.89*10**8:
            comment = "In the Asteroid Belt. OSHA guidelines suggest wearing a helmet."
        elif distance < 7.78*10**8:
            comment = "Stuck between a bunch of rocks and a hard place. (the hard place is Jupiter)"
        elif distance < 7.82*10**8:
            comment = "You better leave Jupiter's orbit before you succumb to its pull."
        elif distance < 1.42*10**9:
            comment = "In the middle of two giants."
        elif distance < 1.44*10**9:
            comment = "You've become Saturn's 147th moon. At least you get to see its rings..."
        elif distance < 2.87*10**9:
            comment = "This is like the least interesting planetary gap ever (Saturn - Uranus)"
        elif distance < 2.89*10**9:
            comment = "Haha uranus"
        elif distance < 4.49*10**9:
            comment = 'Trapped in the middle of ice. (or at least what astronomers call "ice")'
        elif distance < 4.51*10**9:
            comment = "In Neptune's orbit, you get to be disappointed at how not-blue it looks."
        elif distance < 6.08*10**9:
            comment = "Pretty boring around here; further than all the planets, but not far enough to get to the meat of the Kuiper Belt. Oh well."
        elif distance < 6.1*10**9:
            comment = "Pluto; the most planet non-planet out there. (Or the least planet planet, depending on how you look at it.)"
        elif distance < 6.2*10**9:
            comment = "Further than Pluto."
        elif distance < 7.48*10**9:
            comment = "Kuiper Belt. Welcome to comet-land."
        elif distance < 1.49*10**10:
            comment = "You can barely see the Sun anymore. It's just a speck. Yet you're still bound by its gravity, and by its solar wind. Stupid Sun."
        elif distance < 2.99*10**11:
            comment = choice([
                        "Nobody knows what goes on here. Maybe there's a 9th planet. Or a 10th. Maybe even an 11th.",
                        "Finally free from radiation. Now all you have to deal with are giant asteroids. Shouldn't be that hard."
                      ])
        elif distance < 2.99*10**13:
            comment = "Welcome to the giant Oort cloud. Enjoy your stay."
        elif distance < 4.02*10**13:
            comment = "Outside the Solar System, in the void between stars..."
        elif distance < 6.623*10**14:
            comment = "The Milky Way sure is nice this time of year"
        elif distance < 1.325*10**17:
            comment = "What Sun?"
        elif 2.5*10**17 < distance < 2.6*10** 17:
            comment = "You're in a black hole now. What's it like?"
        elif distance < 10**100:
            comment = "You've officially escaped the galaxy. Great job."
        elif distance < 10**1000:
            comment = "You're too far to be detected!"
        else:
            comment = "what"

        if distance < 9.46*10**12:
            dist_text = f"{distance:,} km"
        else:
            dist_text = f"{distance/(9.46*10**12):,.2f} ly"

        #draw image
        fnt = ImageFont.truetype("assets/Raleway.ttf", 32)
        fnt.set_variation_by_axes([400]) # set font weight
        wrapped_comment = get_wrapped_text(comment, fnt, 600)
        if wrapped_comment.count("\n") > 1:
            fnt = ImageFont.truetype("assets/Raleway.ttf", 24)
            fnt.set_variation_by_axes([500])
            wrapped_comment = get_wrapped_text(comment, fnt, 600)

        large_fnt = ImageFont.truetype("assets/Raleway.ttf", 48)
        large_fnt.set_variation_by_axes([500])

        img = Image.new("RGBA", (640,640), (0,0,0,255))
        d = ImageDraw.Draw(img)

        #comments
        d.text((320,60), dist_text, font=large_fnt, anchor="ms", fill=(255, 255, 255, 255))
        d.text((320, 100), wrapped_comment, font=fnt, anchor="ms", align="center", fill=(255, 255, 255, 255))

        # other objects
        od_factor = 2 #object distance factor; basically how far you can see objects
        for o in self.objects:
            if distance / od_factor < o < distance * od_factor:
                relative_distance = o/distance
                x = 900*(-relative_distance/od_factor+1)**(log10(3)/log10(od_factor/(od_factor-1))) #weird math ignore it
                oimg = Image.open(self.objects[o]["asset"])
                w, h = oimg.size
                img.alpha_composite(oimg, (round(x-w/2), round(320-h/2)), (0,0))

        #sun
        try:
            x = 780 + log10(distance)*5
        except ValueError:
            x = 780
        d.circle((x,320), radius=250, fill=(0, 0, 0)) #drawn to cover up anything that might be inside the sun
        d.circle((x,320), radius=250, outline=(218, 193, 134), width=20)

        #user avatar
        avatar = await interaction.user.display_avatar.read()
        avimg = Image.open(BytesIO(avatar)).resize((80,80))
        avimg = crop_circle(avimg)
        if distance > 1:
            img.alpha_composite(avimg, (260,280), (0,0))
        elif distance == 1:
            img.alpha_composite(avimg, (400,280), (0,0))
        else:
            img.alpha_composite(avimg, (540,280), (0,0))

        #send
        b = BytesIO()
        img.save(b, "PNG")
        b.seek(0)

        await interaction.response.send_message(file=discord.File(b,"image.png"))

async def setup(client):
    await client.add_cog(DistanceCog(client))
