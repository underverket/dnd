ICONS_RAW = [
    {
        "id": "coffee",
        "name": "Coffee Break",
        "body_color": (40, 26, 13),
        "body": [
            "X X X X X X X X",  # Fill everything with green background
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X"
        ],
        "custom": [
            # dark brown: 40, 26, 13
            # light brown: 101, 67, 33
            # Coffee cup outline in white (moved 1px left)
            {"row": 3, "col": 1, "color": (255, 255, 255)},  # Top left
            {"row": 3, "col": 2, "color": (255, 255, 255)},
            {"row": 3, "col": 3, "color": (255, 255, 255)},
            {"row": 3, "col": 4, "color": (255, 255, 255)},
            {"row": 3, "col": 5, "color": (255, 255, 255)},  # Top right (was col 6)
            
            # Left side of cup
            {"row": 4, "col": 1, "color": (255, 255, 255)},
            {"row": 5, "col": 1, "color": (255, 255, 255)},
            {"row": 6, "col": 1, "color": (255, 255, 255)},
            
            # Right side of cup (moved 1px left)
            {"row": 4, "col": 5, "color": (255, 255, 255)},  # was col 6
            {"row": 5, "col": 5, "color": (255, 255, 255)},  # was col 6
            {"row": 6, "col": 5, "color": (255, 255, 255)},  # was col 6
            
            # Bottom of cup
            {"row": 7, "col": 2, "color": (255, 255, 255)},
            {"row": 7, "col": 3, "color": (255, 255, 255)},
            {"row": 7, "col": 4, "color": (255, 255, 255)},
            
            # Handle (moved 1px left)
            {"row": 4, "col": 6, "color": (255, 255, 255)},  # was col 7
            {"row": 5, "col": 6, "color": (255, 255, 255)},  # was col 7
            
            # Coffee inside (moved 1px left and made 1px narrower)
            {"row": 4, "col": 2, "color": (101, 67, 33)},
            {"row": 4, "col": 3, "color": (101, 67, 33)},
            {"row": 4, "col": 4, "color": (101, 67, 33)},
            {"row": 5, "col": 2, "color": (101, 67, 33)},
            {"row": 5, "col": 3, "color": (101, 67, 33)},
            {"row": 5, "col": 4, "color": (101, 67, 33)},
            {"row": 6, "col": 2, "color": (101, 67, 33)},
            {"row": 6, "col": 3, "color": (101, 67, 33)},
            {"row": 6, "col": 4, "color": (101, 67, 33)},
        ],
        "animations": [
            {
                "name": "steam",
                "interval": 1200,
                "frame_duration": 200,
                "reverse": True,
                "color": (101, 67, 33),
                "frames": [
                    [
                        "_ _ X _ X _ _ _",
                        "_ _ _ X _ X _ _",
                        "_ _ X _ X _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _"
                    ],
                    [
                        "_ _ _ X _ X _ _",
                        "_ _ _ X _ X _ _",
                        "_ _ X _ X _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _"
                    ],
                    [
                        "_ _ _ X _ X _ _",
                        "_ _ X _ X _ _ _",
                        "_ _ X _ X _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _"
                    ],
                    [
                        "_ _ X _ X _ _ _",
                        "_ X _ X _ _ _ _",
                        "_ _ X _ X _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _"
                    ],
                    [
                        "_ X _ X _ _ _ _",
                        "_ X _ X _ _ _ _",
                        "_ _ X _ X _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _"
                    ],
                    [
                        "_ X _ X _ _ _ _",
                        "_ _ X _ X _ _ _",
                        "_ _ X _ X _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _"
                    ],
                ]
            }
        ]
    }
]