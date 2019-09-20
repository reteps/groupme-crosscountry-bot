# groupme-crosscountry-bot

A heroku template for creating a groupme cross country bot.

![Image of graph](https://i.imgur.com/t5JeON3.png "Example Image")

## Setup

- [ ] Clone this repository
- [ ] Create a groupme developer bot, use a random callback URL
- [ ] Add your groupme bot id to graph.py under `GROUPME_BOT_ID`
- [ ] Add your personal image uploading token to graph.py under `GROUPME_IMAGE_SERVICE_TOKEN`
- [ ] Setup heroku
    - [ ] Install heroku
    - [ ] `heroku create` - make a note of the URL
    - [ ] `git add .; git commit -am "Added Token"`
    - [ ] `git push heroku master`
- [ ] Add the new callback URL to groupme bot

## Usage

In the chat, `graph name`.

If the name doesn't come up, try adding your school at the end, ie. `graph name school`
