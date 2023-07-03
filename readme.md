# Poszukiwanie najkrótszej ścieżki
## Wstęp
Projekt miał na celu stworzenie programu który wczyta obraz mapy gdzie drogi są jaśniejsze niż tło, pozwoli wybrać dwa punkty a następnie zwróci najkrótszą ścieżkę między nimi uwzględniając przy tym szerokości dróg po jakich będzie się poruszać.
## Instrukcja obsługi
Na początek należy zainstalować potrzebne biblioteki. Można to zrobić za pomocą następującej komendy:
```
python -m pip install -r requirements.txt
```
Następnie procedura jest następująca:
1) Wykonujemy program podając mu ścieżkę do obrazu mapy (png lub gif) oraz opcjonalnie interwał po jakim ma pokazywać jaką część mapy już sprawdziliśmy. Przykładowa komenda wygląda następująco: `python main.py ./maps/map1.png --interval 5000`
2) Po wykonaniu komendy wyświetli nam się okno z mapą. W tym oknie należy wybrać dwa punkty pomiędzy którymi chcemy znaleźć najkrótszą ścieżkę.
3) Zgodnie z wybranym interwałem program wyświetli najpierw ile mapy jeszcze zostało do zwiedzenia a następnie ile mapy już zwiedziliśmy.
4) Na koniec jak już program znajdzie najkrótszą ścieżkę wyświetli ją na mapie.