import time

channels = [
    {
        'id': 'C0184982',
        'creator': 'U0384230',
        'name': 'trotskyists',
        'purpose': {'value': "Discussion of revolutionary channel cleanup tactics."},
        'created': int(time.time()) - 30
    },
    {
        'id': 'C0932792',
        'creator': 'U01974322',
        'name': 'gorbavites',
        'purpose': {'value': "Discussion of post-Soviet channel cleanup tactics."},
        'created': int(time.time()) - 10
    },
    {
        'id': 'C0932792',
        'creator': 'U023BECGF',
        'name': 'leninists',
        'purpose': {'value': "Discussion of the Red channel revolution."},
        'created': int(time.time()) - 86400 * 30
    },
    {
        'id': 'C0932792',
        'creator': 'U012742',
        'name': 'stalinists',
        'purpose': {'value': "Discussion of channel pogroms."},
        'created': int(time.time()) - 86400 * 60
    },
    {
        'id': 'C0133272',
        'creator': 'U012742',
        'name': 'zmeta-control',
        'purpose': {'value': "The illusion thereof."},
        'created': int(time.time()) - 86400 * 75
    },
    {
        'id': 'C0133272',
        'creator': 'U012742',
        'name': 'zmeta-new-channels',
        'purpose': {'value': "New channel annoucements."},
        'created': int(time.time()) - 86400 * 90
    }
]


emoji = {
    "ok": True,
    "emoji": {
        "floppy_disk": "http://example.com/example.png"
    }
}


messages = [
    {
        "type": "message",
        "user": "U01974322",
        "text": "flag content rule saver &gt;1 :floppy_disk: <#C0932792|gorbavites>",
        "ts": "1498076539.987000",
        "channel": "trotskyists"
    },
    {
        "type": "message",
        "user": "U012742",
        "text": "Hi",
        "ts": "1498076715.048882",
        "channel": "trotskyists"
    },
    {
        "type": "message",
        "user": "U012742",
        "text": "Hi",
        "ts": "1498076748.060328",
        "channel": "trotskyists"
    },
    {
        "type": "message",
        "user": "U0384230",
        "text": "Flag me, please.",
        "ts": "1498077206.225653",
        "channel": "trotskyists",
        "reactions": [
            {
                "name": "floppy_disk",
                "users": [
                    "U023BECGF",
                    "U012742"
                ],
                "count": 2
            }
        ]
    },
    {
        "type": "message",
        "user": "U023BECGF",
        "text": "Hi.",
        "ts": "1498079094.888214",
        "channel": "trotskyists"
    }
]


users = [
    {
        "id": "U023BECGF",
        "name": "lenin",
        "real_name": "Vladimir Ilyich Ulyanov",
        "is_admin": True,
        "is_owner": True,
        "updated": 1490054400,
        "has_2fa": False
    },
    {
        "id": "U0384230",
        "name": "trotsky",
        "real_name": "Leon Trotsky",
        "is_admin": True,
        "is_owner": True,
        "updated": 1490054400,
        "has_2fa": False
    },
    {
        "id": "U012742",
        "name": "stalin",
        "real_name": "Joseph Vissarionovich Stalin",
        "is_admin": True,
        "is_owner": True,
        "updated": 1490054400,
        "has_2fa": False
    },
    {
        "id": "U01974322",
        "name": "gorbachev",
        "real_name": "Mikhail Gorbachev",
        "is_admin": True,
        "is_owner": True,
        "updated": 1490054400,
        "has_2fa": False
    }
]
