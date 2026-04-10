```markdown
# echomesh

p2p messenger. no fucking servers. u r welcome, asshole.

## what the fuck u get

- 🔒 encrypted as fuck (aes-128)
- 🚫 no server bullshit - direct dick to dick connection
- 👑 admin commands (kick, announce - be a fucking dictator)
- 🔐 password that shit - keep weirdos out
- 📜 history cuz ur memory sucks
- ✏️ typing indicator - so u know they're ignoring ur dumb ass

## looks like this shit

```
[22:15:30] bro: sup fucker
[22:15:32] → not much dickhead

┌─u ─────────────────────────────────
└> 
```

## install (it's not fucking hard)

```bash
git clone https://github.com/ur_dumb_ass/echomesh.git
cd echomesh
python3 -m venv venv
source venv/bin/activate  # fucking do it
pip install cryptography  # only one dependency, stop crying
python3 echomesh.py
```

## how the fuck to use this

**host:** pick 1, set password if u r paranoid, give ur ip to the other loser

**connect:** pick 2, type their fucking ip, password if they set one

## commands (read them or fuck off)

| command | what the fuck it does |
|---------|----------------------|
| `/quit` | gtfo u coward |
| `/me` | do some dumb shit like `/me cries like a bitch` |
| `/status` | shows connection crap |
| `/history` | last messages u already forgot |
| `/kick` | admin - yeet that motherfucker out |
| `/announce` | admin - yell at everyone like an asshole |

## how this piece of shit works

```
[ur pc] ←─── encrypted fucking magic ───→ [friend's shitty pc]
     (no servers, no middlemen, no fucking around)
```

## requirements (don't cry to me)

- python 3.8+ (upgrade ur garbage)
- cryptography (pip installs it, figure it out)
- open port 8888 if ur hosting (or change it, idgaf)

## internet access (for u long distance bitches)

use ngrok u fucking noob:

```bash
# on host machine
ngrok tcp 8888

# give that gay ass address to ur friend
```

## license

gnu gpl 3.0
