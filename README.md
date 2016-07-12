# kodi-skill
A Mycroft skill which facilitates the controlling of a remote (or local) kodi instance through voice commands

# Setup
copy this project to ~/.mycroft/third_party_skills/

# Configuration

Add the following section to your mycroft-core/mycroft/configuration/mycroft.ini file
```
[KodiSkill]
protocol = "http"
host = "<kodi-host>"
port = 80
similarity_threshold_percentage = 75
```

Also make sure your kodi is setup to be controlled via http interface
