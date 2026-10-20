# backend-python
Backend in Python

Instalar ambiente
python3 -m venv venv

Activar ambiente

linux
source venv/bin/activate

windows
.\venv\Scripts\Activate.ps1


Instalar librerias
pip install --upgrade pip
pip install -r requirements.txt

Iniciar aplicacion
uvicorn app.main:app --reload

Probar api plataforma
http://localhost:8000/platforms/


{"data":[{"description":"Microsoft Xbox 360","url":"/x360","id":63},{"description":"Microsoft Xbox One","url":"/xone","id":64},{"description":"Nintendo Entertainment System (NES)","url":"/nes","id":76},{"description":"Sony Playstation","url":"/ps1","id":118},{"description":"Sony Playstation 2","url":"/ps2","id":119},{"description":"Sony Playstation 3","url":"/ps3","id":120},{"description":"Sony Playstation 4","url":"/ps4","id":121},{"description":"Sony Playstation 5","url":"/ps5","id":122},{"description":"Super Nintendo (SNES)","url":"/snes","id":126}],"pagination":{"currentPage":1,"perPage":10,"totalRecords":9,"totalPages":1}}

http://localhost:8000/games/

{"data":[{"id":16489,"title":"The Witcher 3: Wild Hunt","platform":"Sony Playstation 4"},{"id":17111,"title":"The Witness","platform":"Sony Playstation 4"}],"pagination":{"currentPage":0,"perPage":100,"totalRecords":2,"totalPages":1}}

http://localhost:8000/games/random

{"id":16489,"title":"The Witcher 3: Wild Hunt","platform":"Sony Playstation 4","publisher":"CD Projekt","releasedate":"2015-05-19","players":"1","genre":"RPG","imageOriginal":"https://images.example.com/witcher3.jpg","youtubeTrailer":"https://www.youtube.com/embed/c0i88t0Kacs"}


http://localhost:8000/reviews/123

[{"name":"Armchair Empire","date":"","review":"Provides an excellent source of platforming at a very moderate price tag. There can&#146;t be enough good said about this title as it serves as a remake of one of the early titles that changed the face of gaming forever.","score":"85","source":"Metacritic","id_game":123,"id":3670},{"name":"Nintendo Power","date":"","review":"A perfect primer for the rest of the Metroid series. [Dec 2004, p.148]","score":"84","source":"Metacritic","id_game":123,"id":3671},{"name":"GameCube Advanced","date":"","review":"A great game worthy of the Classic line, but the difficulty will turn off many prospective gamers.","score":"70","source":"Metacritic","id_game":123,"id":3672},{"name":"Nintendojo","date":"","review":"Frankly speaking, it's one of the best titles from the NES years. However, the game has been ported so many times that it hardly stands on its own as a stand-alone experience.","score":"69","source":"Metacritic","id_game":123,"id":3673},{"name":"IGN","date":"","review":"The only reason to spend 20 bills on this one is if you have no interest in zipping through the awesome GBA remake, \\Metroid: Zero Mission,\\ or simply want to complete the Classic NES collection. It's not worth the purchase otherwise.","score":"60","source":"Metacritic","id_game":123,"id":3674},{"name":"GameSpot","date":"","review":"It's easy to see how certain aspects of Metroid's design made it a classic, but 18 years later, the overall package just doesn't measure up to today's action adventure standards.","score":"52","source":"Metacritic","id_game":123,"id":3675},{"name":"1UP","date":"","review":"For $10 more, you can get the exact same thing in the form of a free bonus [in \\Metroid: Zero Mission\\] with a top-notch remake of the game that brings its graphics, level design and story up to contemporary standards along with a cool bonus section that serves as a valuable prelude to the subsequent games. Now which one would you rather have? Think hard, now.","score":"50","source":"Metacritic","id_game":123,"id":3676},{"name":"Play Magazine","date":"","review":"If you want Metroid, get \\Zero Mission\\ instead. [Dec 2004, p.100]","score":"50","source":"Metacritic","id_game":123,"id":3677},{"name":"Cheat Code Central","date":"Air Date","review":"You would be better off spending a few extra bucks and getting the \\Zero Mission\\ game if you don't already have it. Otherwise I would be very hesitant to spend the twenty bucks on this old clunker.","score":"30","source":"Metacritic","id_game":123,"id":3678},{"name":"","date":"2024-07-04","review":"I don't believe this game age well at all. At the point that today i don't even consider it a good game. No map, unfair difficulty. But at least this is the first game of one of my favorite franchises and it has most of those things that i love about it","score":"6","source":"Metacritic User","id_game":123,"id":951421},{"name":"","date":"2024-05-04","review":"this game kinda blows, still a start of something great so points for that ig","score":"5","source":"Metacritic User","id_game":123,"id":951422},{"name":"","date":"2023-12-17","review":"This game was fun. For the NES era, it had great exploration and a creepy atmosphere that I liked. It was really difficult, easy to get lost without a map, and the controls themselves feel a little stiff. Not the greatest game ever, but still a decent start to the series.","score":"6","source":"Metacritic User","id_game":123,"id":951423},{"name":"","date":"2023-05-11","review":"--\\u003E Pro's:\\r\\n* Fun side scroller Adventure game\\r\\n* Easy to Learn the controls\\r\\n* Good Story\\r\\n\\r\\n--\\u003E Cons\\r\\n* YOU'RE A FEMALE??? I THOUGHT I WAS A FANCY ROBOT THING","score":"9","source":"Metacritic User","id_game":123,"id":951424},{"name":"","date":"2021-02-11","review":"I played this game on the NES and I can say that things really haven't changed.  I will always prefer this version over Zero mission on GBA. The original soundtrack is one of my favorites, and every time I  wake up I hear the ENTER SAMUS jingle. I will always prefer the NES version over this one, but if you have a GBA then this is the best way to play. I still have fond memories of climbing as fast as I could in Brinstar, and discovering the energy tank for the first time. Metroid is also the perfect length for a handheld console, It's around 4 to 5 hours of gameplay, and this is if you make your way to Mother Brain on the first try.\\r\\n\\r\\nI recommend Metroid on any platform (Except Wii and Wii U)","score":"10","source":"Metacritic User","id_game":123,"id":951425},{"name":"","date":"2021-02-08","review":"I played this back in the day. It was one tough non linear game but the toughness came from not having a map and the saves not working. t was a game unlike super mario and stuff aimed at more mature players. Solid 10 and one of the best nes games. you shouldnt buy it now because its dated obviously but if they remake it somehow with modern graphics grab it. By modern i mean modern 2d graphics not the 3d crap. if i wanted 3d i would play mass effect or grand theft auto","score":"10","source":"Metacritic User","id_game":123,"id":951426},{"name":"","date":"2019-04-29","review":"--\\u003E Pro's:\\r\\n*it's the original classic, which is still a good game.\\r\\n*it used to be cheap new.\\r\\n\\r\\n--\\u003E Cons\\r\\n*there's a remake (zero mission) on the same system.\\r\\n*that very same remake unlocks this game upon completion.\\r\\n*The game has aged.\\r\\n*The game is pretty hard.\\r\\n\\r\\n--\\u003E Conclusion:\\r\\nDo not buy unless collecting the \\NES Classics\\ line of GBA games.","score":"6","source":"Metacritic User","id_game":123,"id":951427},{"name":"","date":"2012-07-16","review":"All the reviews on here are complaining about how this is already on zero **** what if it already on zero mission. This is a fantastic game and needed a release as a stand alone game. The story this game started is amazing and fans of the series or the game.","score":"10","source":"Metacritic User","id_game":123,"id":951428},{"name":"","date":"2011-05-25","review":"If you missed out on the NES release of this, be sure to check this one out. Multiple weapons and massive levels make this a great game to play in the car.","score":"8","source":"Metacritic User","id_game":123,"id":951429}]

http://localhost:8000/docs