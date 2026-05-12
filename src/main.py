import sys
import os
import pygame

# Ensure the src directory is in the path to allow relative imports from the project root 'src'
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from game.engine import GameEngine

def main():
    width, height = 1024, 768
    game = GameEngine(width, height)
    game.run()
    pygame.quit()

if __name__ == "__main__":
    main()
