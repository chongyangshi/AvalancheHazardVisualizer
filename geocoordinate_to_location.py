#Boundaries of locations.
locations = {
    "Torridon" : {
        "start" : [-5.90874227918, 57.310592299],
        "end" : [-5.11817626423, 57.7821005754]
    },
    "Creag Meagaidh" : {
        "start" : [-4.99675917528, 56.7327671068],
        "end" : [-4.20660165144, 57.1985659148]
    },
    "Lochaber" : {
        "start": [-5.39304342471, 56.5796588786],
        "end" : [-4.6110949438, 57.0479096187]
    },
    "Glencoe" : {
        "start" : [-5.30671228924, 56.3790416259],
        "end" : [-4.52777017063, 56.8467419929]
    },
    "Southern Cairngorms" : {
        "start" : [-3.78318124708, 56.6893284359],
        "end" : [-2.97874558556, 57.1474411178]
    },
    "Northen Cairngorms" : {
        "start" : [-4.06469864678, 56.9024363754],
        "end" : [-3.25917673638, 57.3623462403]
    }
}

def get_location_name(latitude, longitude):
    ''' Given a geodetic coordinate, return the name of location.
        Nondeterministic when a coordinate fits in more than one 
        location. Returns empty string if not found. '''
    
    found = False
    for l in locations:
        if (longitude > locations[l]["start"][0]) and ((longitude < locations[l]["end"][0])):
            if (latitude > locations[l]["start"][1]) and ((longitude < locations[l]["end"][1])):
                found = True
                return l
    
    if not found:
        return ""