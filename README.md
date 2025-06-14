# fast-chess-game-service

How to run server:

```bash
docker build -t books_service .
docker run  -d -p 8000:8000 -v /home/pawel/Desktop/backend/db:/app/db -v /home/pawel/Desktop/backend/logs:/app/logs -v /home/pawel/Desktop/backend/media:/app/media <image-id>
```
