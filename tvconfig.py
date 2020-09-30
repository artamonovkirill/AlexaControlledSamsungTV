device_name = "Pi" #What shows up under devices in smarttv.tomershemesh.me. not that important unless you have multiple devices (not tvs) on your account
volume_step_size = 5  #how much your tv volume should go up by when you say 'Alexa, turn up the volume on my tv'


tvs = [
    {
        'host': "192.168.1.18", #ip address of tv
        'tv_model' : "UE40H6200", #9 digit tv model located on the back of your tv
        'tv_mac_address': "84:a4:66:fa:67:ef", #mac address of your tv
        'tv_name' : 'TV', #leave as TV to refrence this by just 'TV'. ex: 'Alexa, turn on the TV'.  Change to eg:'Kitchen TV' if you want to say 'Alexa turn on the kitchen TV', You cannot have multiple tvs have the same name
        'prefer_HD': True, #if you say 'change the channel to ESPN',  always attempt to use the HD channel number'
    }
]
