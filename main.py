from src.game import Game
import asyncio

if __name__ == '__main__':
    game = Game()
    asyncio.run(game.run())