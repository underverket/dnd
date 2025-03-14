# "X" = Fill
# "_" = Empty
# 
# Simple Character:
# {
#    "id": "unique_id",
#    "name": "Name",
#    "body": [
#        "X X X X X X X X",
#        "X X X X X X X X",
#        "X X X X X X X X",
#        "X X X X X X X X",
#        "X X X X X X X X",
#        "X X X X X X X X",
#        "X X X X X X X X",
#        "X X X X X X X X"
#    ],
# }
# 
# Add auto highlights and/or shadows (Highlights inherits lighter 
# color from body, shadows inherits darker color from body):
#    "hl": [
#        "X X X X X X X X",
#        "X X X X X X X X",
#        "X X X X X X X X",
#        "X X X X X X X X",
#        "X X X X X X X X",
#        "X X X X X X X X",
#        "X X X X X X X X",
#        "X X X X X X X X"
#    ],
#    "sdw": [
#        "X X X X X X X X",
#        "X X X X X X X X",
#        "X X X X X X X X",
#        "X X X X X X X X",
#        "X X X X X X X X",
#        "X X X X X X X X",
#        "X X X X X X X X",
#        "X X X X X X X X"
#    ],
# 
# Color "Sticky" pixels, these can not be highlighted or shadowed, and will not be affected by status or animations.
# Unfortunatly, you have to place these manually, no visual ASCII representation is available.
#    "custom": [
#        {'row': 4, 'col': 2, 'color': (255, 0, 0)},    # Red
#        {'row': 4, 'col': 5, 'color': (255, 0, 0)},    # Red
#        {'row': 5, 'col': 2, 'color': (255, 127, 0)},  # Orange
#        {'row': 5, 'col': 5, 'color': (255, 127, 0)},  # Orange
#    ],
#
# Fancy an animation? Add an animation object, no limit to frames:
# "animations": [
#     {
#         "name": "uniqiue_animation_name",
#         "interval": 5000, // Pause between animation cycles ms
#         "frame_duration": 50, // Duration of each frame in ms
#         "reverse": False, // If animation should reverse back to first frame.
#         "color": (255, 255, 255), // Color of the animation, no support for multiple colors.
#         "frames": [
#             [   # Example: Frame 1 - Eyes open
#                 "_ _ _ _ _ _ _ _",
#                 "_ _ _ _ _ _ _ _",
#                 "_ _ _ _ _ _ _ _",
#                 "_ _ _ _ _ _ _ _",
#                 "_ _ X _ _ X _ _",
#                 "_ _ X _ _ X _ _",
#                 "_ _ _ _ _ _ _ _",
#                 "_ _ _ _ _ _ _ _"
#             ],
#             [   # Example: Frame 2 - Eyes closed
#                 "_ _ _ _ _ _ _ _",
#                 "_ _ _ _ _ _ _ _",
#                 "_ _ _ _ _ _ _ _",
#                 "_ _ _ _ _ _ _ _",
#                 "_ _ _ _ _ _ _ _",
#                 "_ _ X _ _ X _ _",
#                 "_ _ _ _ _ _ _ _",
#                 "_ _ _ _ _ _ _ _"
#             ]
#         ]
#     }
# ]

CHARACTERS_RAW = [
    {
        "id": "ghost_plain",
        "name": "Plain Ghost",
        "body": [
            "_ _ X X X X _ _",
            "_ X X X X X X _",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X _ X _ X _ X _"
        ],
        "animations": [
            {
                "name": "blink",
                "interval": 3000,
                "frame_duration": 50,
                "reverse": False,
                "color": (255, 255, 255),
                "frames": [
                    [   # Frame 1 - Eyes open
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ X _ _ X _ _",
                        "_ _ X _ _ X _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _"
                    ],
                    [   # Frame 2 - Eyes half closed
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ X _ _ X _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _"
                    ],
                    [   # Frame 3 - Eyes closed
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _"
                    ]
                ]
            }
        ]
    },
    {
        "id": "heart",
        "name": "Heart",
        "body": [
            "_ _ _ _ _ _ _ _",
            "_ X X _ _ X X _",
            "X X X X X X X X",
            "X X X X X X X X",
            "_ X X X X X X _",
            "_ _ X X X X _ _",
            "_ _ _ X X _ _ _",
            "_ _ _ _ _ _ _ _"
        ],
        "animations": [
            {
                "name": "blink_heart",
                "interval": 7000,
                "frame_duration": 50,
                "reverse": False,
                "color": (255, 255, 255),
                "frames": [
                    [   # Frame 1 - Eyes open
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ X _ _ X _ _",
                        "_ _ X _ _ X _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _"
                    ],
                    [   # Frame 2 - Eyes half closed
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ X _ _ X _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _"
                    ],
                    [   # Frame 3 - Eyes closed
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _"
                    ]
                ]
            }
        ],
        "hl": [
            "_ _ _ _ _ _ _ _",
            "_ _ _ _ _ X X _",
            "_ _ _ _ _ _ X X",
            "_ _ _ _ _ _ _ X",
            "_ _ _ _ _ _ _ _",
            "_ _ _ _ _ _ _ _",
            "_ _ _ _ _ _ _ _",
            "_ _ _ _ _ _ _ _"
        ],
        "sdw": [
            "_ _ _ _ _ _ _ _",
            "_ _ _ _ _ _ _ _",
            "_ _ _ _ _ _ _ _",
            "X _ _ _ _ _ _ _",
            "_ X _ _ _ _ _ _",
            "_ _ X _ _ _ _ _",
            "_ _ _ X _ _ _ _",
            "_ _ _ _ _ _ _ _"
        ],
    },
    {
        "id": "invader",
        "name": "Space Invader",
        "body": [
            "_ X _ _ _ _ X _",
            "_ _ X X X X _ _",
            "_ X X X X X X _",
            "X X X X X X X X",
            "_ X X X X X X _",
            "_ X _ _ _ _ X _",
            "_ _ X _ _ X _ _",
            "_ _ _ _ _ _ _ _"
        ],
        "animations": [
            {
                "name": "blik_invader",
                "interval": 7000,
                "frame_duration": 50,
                "reverse": False,
                "color": (255, 255, 255),
                "frames": [
                    [   # Frame 1 - Eyes open                        
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ X _ _ X _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _"
                    ],
                    [   # Frame 2 - Eyes half closed
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _"
                    ],
                ]
            }
        ],
    },
    {
        "id": "creeper",
        "name": "Creeper",
        "body": [
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X"
        ],
        "animations": [
            {
                "name": "blik_invader",
                "interval": 7000,
                "frame_duration": 50,
                "reverse": False,
                "color": (255, 255, 255),
                "frames": [
                    [   # Frame 1 - Eyes open                        
                        "_ _ _ _ _ _ _ _",
                        "_ X X _ _ X X _",
                        "_ X X _ _ X X _",
                        "_ _ _ X X _ _ _",
                        "_ X X X X X X _",
                        "_ X X X X X X _",
                        "_ X _ _ _ _ X _",
                        "_ _ _ _ _ _ _ _"
                    ],
                    [   # Frame 2 - Eyes half closed
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ X X _ _ X X _",
                        "_ _ _ X X _ _ _",
                        "_ X X X X X X _",
                        "_ X X X X X X _",
                        "_ X _ _ _ _ X _",
                        "_ _ _ _ _ _ _ _"
                    ],
                    [   # Frame 3 - Eyes shut
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ X X _ _ _",
                        "_ X X X X X X _",
                        "_ X X X X X X _",
                        "_ X _ _ _ _ X _",
                        "_ _ _ _ _ _ _ _"
                    ],
                ]
            }
        ],
    },
    # {
    #     "id": "fox",
    #     "name": "The Fox",
    #     "body": [
    #         "_ _ _ _ _ X X _",
    #         "X _ X _ _ _ X X",
    #         "X X X _ _ _ _ X",
    #         "X X X X X X X X",
    #         "X X X X X X X X",
    #         "_ X X X X X X X",
    #         "_ X _ X _ X _ X",
    #         "_ X _ X _ X _ X"
    #     ],
    #     "sdw": [
    #         "_ _ _ _ _ _ _ _",
    #         "_ _ _ _ _ _ X X",
    #         "_ _ _ _ _ _ _ X",
    #         "_ _ _ _ _ _ _ _",
    #         "_ _ _ _ _ _ _ _",
    #         "_ _ _ _ _ _ _ _",
    #         "_ X _ _ _ X _ _",
    #         "_ _ _ _ _ _ _ _"
    #     ],
    #     "custom": [
    #         {"row": 0, "col": 5, "color": (195, 126, 74)},  # Tail tip 1 (White)
    #         {"row": 0, "col": 6, "color": (195, 126, 74)},  # Tail tip 2 (White)

    #         {"row": 4, "col": 0, "color": (50, 50, 50)},  # Nose (Dark Gray)

    #         {"row": 1, "col": 0, "color": (195, 126, 74)},  # Left Ear Tip (Brown)
    #         {"row": 1, "col": 2, "color": (195, 126, 74)},  # Right Ear Tip (Brown)

    #         {"row": 7, "col": 1, "color": (195, 126, 74)},  # Left Front Foot (Brown)
    #         {"row": 7, "col": 3, "color": (195, 126, 74)},  # Right Front Foot (Brown)
    #         {"row": 7, "col": 5, "color": (195, 126, 74)},  # Left Back Foot (Brown)
    #         {"row": 7, "col": 7, "color": (195, 126, 74)},  # Right Back Foot (Brown)
    #     ],
    # },
    {
        "id": "cat",
        "name": "The Cat",
        "body": [
            "_ _ _ _ _ _ X _",
            "_ X _ X _ X _ X",
            "_ X X X _ _ _ X",
            "_ X X X X X X X",
            "_ X X X X X X X",
            "_ X X X X X X X",
            "_ X X X X X X X",
            "_ _ _ _ _ _ _ _"
        ],
        "hl": [
            "_ _ _ _ _ _ _ _",
            "_ _ _ _ _ X _ _",
            "_ _ _ _ _ _ _ _",
            "_ _ _ _ _ _ _ _",
            "_ _ _ _ _ _ _ _",
            "_ _ X _ _ _ _ _",
            "_ _ _ _ _ _ _ _",
            "_ _ _ _ _ _ _ _"
        ],
        "sdw": [
            "_ _ _ _ _ _ _ _",
            "_ _ _ _ _ _ _ _",
            "_ _ _ _ _ _ _ _",
            "_ _ _ _ X _ X _",
            "_ _ _ _ X _ X _",
            "_ _ _ _ _ _ _ _",
            "_ _ _ _ X X _ _",
            "_ _ _ _ _ _ _ _"
        ],
        "animations": [
            {
                "name": "cat_walk",
                "interval": 1200,
                "frame_duration": 300,
                "reverse": False,
                "color": (0, 0, 0),
                "frames": [
                    [   # Frame 1                    
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "X _ X _ X _ X _",
                        "_ _ _ _ _ _ _ _"
                    ],
                    [   # Frame 2
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "X _ X X X _ X X",
                        "_ _ _ _ _ _ _ _"
                    ],
                    [   # Frame 3                       
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "X _ X _ X _ X _",
                        "_ _ _ _ _ _ _ _"
                    ],
                    [   # Frame 4                     
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "X X X _ X X X _",
                        "_ _ _ _ _ _ _ _"
                    ],
                ]
            }
        ],
        "custom": [
            {"row": 7, "col": 0, "color": (195, 126, 74)},
            {"row": 7, "col": 1, "color": (195, 126, 74)},
            {"row": 7, "col": 2, "color": (195, 126, 74)},
            {"row": 7, "col": 3, "color": (195, 126, 74)},
            {"row": 7, "col": 4, "color": (195, 126, 74)},
            {"row": 7, "col": 5, "color": (195, 126, 74)},
            {"row": 7, "col": 6, "color": (195, 126, 74)},
            {"row": 7, "col": 7, "color": (195, 126, 74)},
        ],
    },
    {
        "id": "cat2",
        "name": "The Sitting Cat",
        "body": [
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X"
        ],
        "animations": [
            {
                "name": "cat_blink",
                "interval": 7000,
                "frame_duration": 50,
                "reverse": False,
                "color": (255, 255, 0),
                "frames": [
                    [   # Frame 1 - Eyes open                        
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ X _ X _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _"
                    ],
                    [   # Frame 2 - Eyes half closed
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _",
                        "_ _ _ _ _ _ _ _"
                    ],
                ]
            }
        ],
        "custom": [
            {"row": 2, "col": 1, "color": (20, 20, 20)},
            {"row": 2, "col": 4, "color": (20, 20, 20)},

            {"row": 3, "col": 1, "color": (20, 20, 20)},
            {"row": 3, "col": 2, "color": (20, 20, 20)},
            {"row": 3, "col": 3, "color": (20, 20, 20)},
            {"row": 3, "col": 4, "color": (20, 20, 20)},

            {"row": 4, "col": 1, "color": (20, 20, 20)},
            {"row": 4, "col": 2, "color": (20, 20, 20)},
            {"row": 4, "col": 3, "color": (20, 20, 20)},
            {"row": 4, "col": 4, "color": (20, 20, 20)},

            {"row": 5, "col": 1, "color": (20, 20, 20)},
            {"row": 5, "col": 2, "color": (20, 20, 20)},
            {"row": 5, "col": 3, "color": (20, 20, 20)},
            {"row": 5, "col": 4, "color": (20, 20, 20)},
            {"row": 5, "col": 6, "color": (50, 50, 50)},
            {"row": 5, "col": 7, "color": (20, 20, 20)},

            {"row": 6, "col": 2, "color": (20, 20, 20)},
            {"row": 6, "col": 3, "color": (20, 20, 20)},
            {"row": 6, "col": 4, "color": (20, 20, 20)},
            {"row": 6, "col": 5, "color": (20, 20, 20)},
            {"row": 6, "col": 7, "color": (20, 20, 20)},

            {"row": 7, "col": 2, "color": (50, 50, 50)},
            {"row": 7, "col": 3, "color": (20, 20, 20)},
            {"row": 7, "col": 4, "color": (50, 50, 50)},
            {"row": 7, "col": 5, "color": (20, 20, 20)},
            {"row": 7, "col": 6, "color": (20, 20, 20)},
            {"row": 7, "col": 7, "color": (20, 20, 20)},
        ],
    },
    {
        "id": "goose",
        "name": "The Goose",
        "body": [
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X",
            "X X X X X X X X"
        ],
        "animations": [
            {
                "name": "squack",
                "interval": 11000,
                "frame_duration": 500,
                "reverse": False,
                "color": (255, 255, 255),
                "frames": [
                    [
                        "_ X X _ _ _ _ _",
                        "_ _ X _ _ _ _ _",
                        "_ _ X _ _ _ _ _",
                        "_ _ X _ _ _ _ _",
                        "_ _ X X X _ _ _",
                        "_ _ X X X X X _",
                        "_ _ _ X X _ _ _",
                        "_ _ _ _ _ _ _ _"
                    ],
                    [
                        "_ X X _ _ _ _ _",
                        "_ _ X _ _ _ _ _",
                        "_ _ X _ _ X X X",
                        "_ _ X X X X X _",
                        "_ _ X X X X _ _",
                        "_ _ X X X X X _",
                        "_ _ _ X X _ _ _",
                        "_ _ _ _ _ _ _ _"
                    ],                    
                ]
            }
        ],
        "custom": [
            {"row": 1, "col": 0, "color": (255, 127, 0)},
            {"row": 1, "col": 1, "color": (255, 127, 0)},
            {"row": 7, "col": 3, "color": (255, 127, 0)},
            {"row": 7, "col": 4, "color": (255, 127, 0)},

            {"row": 5, "col": 7, "color": (140, 140, 140)},
            {"row": 6, "col": 2, "color": (140, 140, 140)},
            {"row": 6, "col": 6, "color": (140, 140, 140)},
            {"row": 6, "col": 5, "color": (140, 140, 140)},
        ],
    },
]
