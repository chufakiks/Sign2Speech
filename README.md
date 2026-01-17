This is a sign language recognition application based on https://github.com/sign/translate that I am building as a part of my bachelor's thesis.

To use the webapp, install npm if not installed yet. 

Build frontend:

```
npm run start
```

Build backend. First download SpaMo checkpoint and put it in the backend folder. https://www.dropbox.com/scl/fi/c9khflgxgl96lx919p6oq/spamo.ckpt?rlkey=gp3zmk6jwg9cnf3e2hpw268ih&st=m2mteopt&dl=0

```
cd backend
conda create env -f environment.yaml
conda activate sign2speech
main.py
```
The website should now run on localhost:4200.
