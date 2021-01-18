# TODO:

* Tisk vícesloupcového layoutu - je potřeba spočítat kolik se tam vejde sloupců a podle toho měnit třídu pro css jinak se teď sloupce překrývají. Protože ale používám monospace font tak to můžu spočítat.
* Pokud přeteče píseň na 2 stránky mohl pokud to detekovat a zmenšit font a přepočítat.
* Dvojitý akord
[A]Byly krásný naše [D]plány [Asus4 A] byla jsi můj celej [F#mi]svět

Zde dojde k chybě v zobrazení akordu [Asus4 A] kdy vypadá takhle
A----------------D-----Asus4 A-------------F#mi--Fmi---Emi--
Byly krásný naše plány  byla jsi můj celej svět ++++++++++++
* Rozpoznání refrénové značky u písní s mezerami - pokud začínají všechny sloky mezerami jako např u https://supermusic.cz/skupina.php?action=piesen&idpiesne=1089 nedojde k rozpoznání Refrénové značky :-/
* je potřeba udělat multiakord podle toho co to je začít to zpracovávat
  1. "C(D)" - při opakování refrénu se hraje jiná tónina ...
  1. "Dmi, Ami,.." na samostaném řádku je to vlastně předehra
  1. "Dmi, Ami, ..." na konco sloky je to vlastně mezihra nebo vyhrávka na konci
* nerozpoznává se vícenásobný refrén např "2 x R:" (supermusic 1089)
* Vyřešit zobrazování a výběr alternativních forem akordů pokud vím, že se mají použít (např A5/E hrané na vzchní nebo spodní 4 struny - https://jguitar.com/chord?bass=E&root=A&chord=5th v)
