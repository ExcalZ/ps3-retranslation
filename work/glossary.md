# Glossary and naming decisions

What the Japanese calls things, what the 1991 US release called them, and
what this translation will call them. Decisions are marked; the rest is
reference for the translator. Every JP name here was read from the JP ROM
by `tools/extract_jp.py` (`work/script.json`, `jp` fields), not from memory.

## Characters

| US | JP | notes |
|---|---|---|
| Rhys | ケイン (Kein) | first generation prince of Landen (JP: リーク Leek kingdom) |
| Maia | マーリナ (Marlena) | the amnesiac bride; JP dialogue: マーリナさま |
| Lena | リナ (Lina) | |
| Lyle | ライル (Lyle) | |
| Mieu | ミュー (Myau) | the name of the cat in Phantasy Star I |
| Wren | シーレン (Siren) | "Wren-type cyborg" is JP シーレン タイプ386 |
| Ayn | アイン (Ain) | |
| Thea | ラン (Lan) | |
| Sari | リン (Rin) | |
| Nial | レイン (Lein) | |
| Laya | ライア (Laia) | both the dark goddess of the legend and the daughter; JP: ライア |
| Alair | ? | to read from the script (JP unmatched entries) |
| Ryan | ダン (Dan) | |
| Sean | シーン (Sheen) | |
| Crys | ノイン (Noin) | |
| Adan | フイン (Fuin) | |
| Aron | ルイン (Ruin) | |
| Kara | ルナ (Luna) | both the warrior and the princess |
| Gwyn | ライア | shares Laya's stat record and name in the JP data |
| Miun | ミューン | |
| Siren | サイレン | JP サイレン; Wren is シーレン - different names |
| Lune | ルーン | |
| Rulakir | ? | |
| Orakio | オラキオ | |

**Decision pending:** whether to use the JP names (Kein, Marlena, Lina...) or
keep the US names players know. The PS4 retranslation kept the established
English names where the JP was a transliteration and restored meaning where
the US had invented; the same rule would keep Rhys/Maia/Lena and restore the
technique names below.

## Techniques

The JP names are not the Foi/Zan family of the other games for most of the
list; the US release renamed them to match PS II/IV.

| US | JP | literal |
|---|---|---|
| Foi | フォイエ | Foie |
| Zan | ザン | Zan |
| Gra | グラブト | Gravt? (Grabt) |
| Tsu | バータ | Barta (ice, as in PS I) |
| Res | サンフォース | Sun Force |
| Gires | スターフォース | Star Force |
| Rever | ムーンフォース | Moon Force |
| Anti | シーフォース | Sea Force |
| Ner | ライジング | Rising |
| Rimit | ヌーン | Noon |
| Shiza | フォール | Fall |
| Deban | ナイト | Night |
| Fanbi | ロー | Law |
| Forsa | アンバランス | Unbalance |
| Nasak | バランス | Balance |
| Shu | カオス | Chaos |
| Megido | メギド | Megid |
| Grantz | グランツ | Grantz |
| (Poison) | ドク | poison status, used as a technique record |

The four groups the Technique Distributor shows are JP こうげきの (attack),
バランスの (balance), かいふくの (recovery), じかんの (time) テクニック; the
US called them Melee, Order, Heal, Time.

## Items (the ones that are not transliterations)

| US | JP | literal |
|---|---|---|
| Antidote | アンティポイズン | Antipoison |
| Star Mist | スターアトマイザー | Star Atomizer |
| Moon Dew | ムーンアトマイザー | Moon Atomizer |
| Escapipe | イグザオカリナ | Exa Ocarina |
| Short Swd | へいしのけん | soldier's sword |
| Sword | きしのつるぎ | knight's sword |
| Steel Swd | せいきしのつるぎ | holy knight's sword |
| Sapphire | もりのサファイア | forest sapphire |
| MoonStone / Moon Tear | つきのいし / つきのなみだ | moon stone / moon tear |
| DragnTear | りゅうのなみだ | dragon's tear |
| Snow | ゆきのけっしょう | snow crystal |
| TwinsRuby | ふたごのルビー | twins' ruby |
| PowrTopaz | ちからのトパーズ | topaz of power |
| MstryStar | しんぴのほし | mystery star |
| AquaParts / Sub Parts / AeroParts | マリン / サブマリン / スカイパーツ | Marine / Submarine / Sky Parts |
| LayaPndnt | ライアペンダント | Laya Pendant |

The US item names were cut to nine cells; the item windows are still 8x8
cells here (see STATUS: menu VWF is not done), so the budget is the widest
stock name of each table until that changes.

## Enemies

Mostly different names in the JP (Glop = ジェリー Jelly, the Grinder family
= バズール, Clops = ルーテラ, Dogbot = ヘルアーマー Hell Armour, Amazon =
ナスカ). The full list is in `work/script.json` (`enemies`). Whether to
restore them is a decision for the translation pass; the enemy name window
is fixed-width.

## Places

To be read from the script: the JP dialogue uses different names for the
kingdoms (リーク for Landen's kingdom, サテライト for Azura, "the desert
dome" for Aridia, ...). `work/dialogue.json` has them in context.

## Text conventions

* `{PAGE}` scrolls one line; keep each page to one line after the first
  `{BR}`.
* Speaker labels: the US used `RHYS "..."`; the JP uses `ケイン 「...」`.
  Convention to decide before the translation pass.
* Numbers inserted by the engine (`{NUM:nn}`) are drawn with the digit
  glyphs; budget them as three or four digits.
