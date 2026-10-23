# Notifications on your phone

The runner tells your phone the moment something needs you, screen off and browser closed, through the free ntfy app and the public ntfy.sh ([ADR 31](../.factory/adr/31-notifications-to-a-closed-phone.md)). These steps are for an Android phone. You do them once per machine; `softfield doctor` says whether they're done.

## Set it up
1. On the machine the runner runs on, run `softfield notify setup` once. It writes `[notify] ntfy` in `~/.config/softfield/factory.toml` with a long random topic and prints it: "In the ntfy app, subscribe to the topic: …". Note the topic.
2. On the phone, install **ntfy** from the Play Store and open it.
3. Tap **+**.
4. Type the topic from step 1, exactly.
5. Leave **Use another server** off: the runner sends to ntfy.sh.
6. Tap **Subscribe**.
7. When Android asks whether ntfy may send notifications, allow it.
8. Back on the machine, run `softfield notify test`. "softfield · Notifications work" arrives on the phone within seconds.

## What a notification says
- One line per thing that needs you: the project and what kind of thing it is, never a card's title or a reply's words. For example "softfield · The lead answered you", "softfield · A card is ready for your sign-off", "softfield · A review stopped", "softfield · A ticket needs your decision", "softfield · Claude's reserve: your choice".
- Several things raised at once about one card come as one: "softfield · 3 things need you on one card".
- A tap opens the page where you act: the card's thread for a reply, a sign-off or a stopped review, the Overview for the rest.
- The page opens only on the home Wi-Fi, as the dashboard does. Away from home the notification still arrives; open it once you're back.

## Nothing twice
The dashboard notifies too, while one of its pages is open in front. On the phone, turn the dashboard's own off so each thing comes once, through ntfy:
1. In Chrome on the phone, open the dashboard.
2. Tap the icon left of the address, then **Permissions** (or **Site settings**).
3. Turn **Notifications** off.

A computer's browser keeps its own; turn it off there the same way if you don't want both.

## If the topic leaks
The topic is the only lock: anyone who has it can read the notifications and send fake ones. To change it:
1. On the machine, open `~/.config/softfield/factory.toml` and remove the `[notify]` section (the `[notify]` line and the `ntfy = …` line under it). `softfield notify setup` keeps a topic it finds, so it has to go first.
2. Run `softfield notify setup` again and note the new topic.
3. In the ntfy app, unsubscribe from the old topic and subscribe to the new one (steps 3 to 7 above).
4. Run `softfield notify test` to see it arrive.
