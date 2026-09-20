# Glossary and naming decisions

What the Japanese calls things, what the 1991 US release called them, and
what this translation calls them. **Decided 2026-09-19: the JP names
throughout** - characters, kingdoms, worlds, techniques and items follow the
Japanese, as the Scenery Recalled script did; the 1991 renames are kept only
where the JP is itself a transliteration of them (Lyle, Mieu, Lune, Orakio,
Cille, Shusoran, Agoe, Mystoke, Lensol, Lashute...). Speaker labels keep the
US convention `KEIN "..."`. Every JP name here was read from the JP ROM
by `tools/extract_jp.py` (`work/script.json`, `jp` fields), not from memory.

## Sources

* The JP ROM itself (`work/script.json` `jp` fields, `tools/extract_jp.py`).
* R. Capowski, *All About Phantasy Star III Names* (Scenery Recalled, 2012),
  http://www.sceneryrecalled.com/trans/ps3names.txt - the naming notes of the
  Scenery Recalled script translation, with the reasoning behind each
  choice (kept as `work/analysis/ps3names.txt`). Cited below as [SR].

## Characters

| US | JP | [SR] | notes / decision |
|---|---|---|---|
| Laya | ライア | Laia | **Decided: Laia.** The katakana is ra-i-a; "Laya" would be ライヤ. [SR] notes JP secondary sources sometimes print "Laya". The peoples are then Laians and Orakians. |
| Rhys | ケイン | Kein | **Kein.** Full name Kein Sa Riik; Kein Le Cille once he marries Marina. |
| Maia | マーリナ | Marina | **Marina** ([SR] first used Marlena; the minstrel's "girl of the sea"). |
| Lena | リナ | Lena | **Lena**, as [SR] ("Rina" may be intended; Lena + Kein -> Lein). |
| Lyle | ライル | Lyle | full name ライル。ラ。ミラー, rendered Lyle La Miller (ミラー is the usual katakana for Miller) |
| Mieu | ミュー | Mieu | the cat's name in PS I (Myau) |
| Wren | シーレン | Searren | **Searren** (33 px, inside the 40 px party-name budget); "Searren type 386 system"; Marine / Aqua / Sky Searren for the transformations. |
| Ayn | アイン | Ain | **Ain** Le Cille; all seven male leads end in -in (Kein, Ain, Lein, Shiin, Noin, Fuin, Luin). |
| Thea | ラン | Lann | **Lann** La Miller, Lyle's daughter |
| Sari | リン | Lynn | **Lynn** No Satera; [SR] pairs Lann/Lynn as Ain's rival brides |
| Nial | レイン | Lein | **Lein** Sa Riik (Lena + Kein) |
| Laya (daughter) / Gwyn | ライア | Laia | shares the mother's name and stat record |
| Alair | ルイセ | Luise | **Luise**; [SR]: Luin = LUise + LeIN |
| Ryan | ダン | Dan | **Dan** Ka Shium |
| Sean | シーン | Shiin | **Shiin** Le Cille |
| Crys | ノイン | Noin | **Noin** No Satera |
| Adan | フイン | Fuin | **Fuin** Sa Riik (the character book prints "Fin") |
| Aron | ルイン | Luin | **Luin** Sa Riik |
| Kara | ルナ | Luna | **Luna** Kay Eshyr, both records |
| Miun | ミューン | Miun | |
| Siren | サイレン | Siren | not the same name as Wren's シーレン |
| Lune | ルーン | Lune | Lune Kay Eshyr; "heir of the house of Eshyr" |
| Orakio | オラキオ | Orakio | |
| Quist | クイスト | Quisto | Lott's village chief in later generations; his wife is エリナ Elina |
| Rulakir | ルラキル | Rulakir | Orakio's elder twin |
| (king of Riik) | サイキ。サ。リーク | - | Saiki Sa Riik, Kein's father, named only in the escapipe notice |
| (minstrel) | マイ | - | Mai, the minstrel of Rysel |
| (Palman heroes) | オハリオ / アイナ | - | Ohario and Aina, in Foundry's history |

[SR] also reads the middle syllable of the nobles' full names (Kein Sa Riik,
Lynn No Satera, Lune Kay Eshyr) as a surname particle, not a middle initial.

## Places

Decided with the character names: the JP names, transliterated where they
are made-up words.

| US | JP | here |
|---|---|---|
| Landen (kingdom, castle) | リーク | Riik |
| Satera | サテラ | Satera |
| Cille / Shusoran / Agoe | シール / シューソラン / アゴエ | Cille / Shusoran / Agoe |
| Yaata / Ilan / Rysel | ヤータ / ヒューリ / ライスル | Yaata / Hyurri / Rysel |
| Hazatak | ハサタカ | Hazatak |
| Aridia | さばくの ドーム | the desert dome / the desert world |
| Techna | フロトラーン, 「ちからの しろ」 | Frotrahn, the Castle of Power |
| Endora | ロット, 「たくみの むら」 | Lott, the artisans' village |
| Lensol | レンソル | Lensol, the castle of lost technology |
| Divisia | グランディレクタ, 「えいこうの」 | Grandirecta (glorious Grandirecta; north and south towns) |
| Aerone | パイロッタ, 「みちびきの むら」 | Pilotta, the guiding village of the pilots |
| New Mota | ファウンダウリ, 「ひそやかな むら」 | Foundry, the hidden village ([SR]) |
| Mystoke | マイストーク, 「せいじゃくの しろ」 | Mystoke, the Castle of Silence |
| Lashute | ラシュート, 「せいなる／じゃあくなる みやこ」 | Lashute, the holy city / the city of evil |
| Skyhaven | 「サマヨエル クランクレアノ シロ」 | Crancrea, the wandering castle |
| Sage Isle | けんじゃの しま | the Isle of the Sage |
| Frigidia | ゆきの せかい | the world of snow |
| Azura | サテライト 「あおの つき」 | Satellite, the Blue Moon |
| Dahlia | 「むらさきの つき」 | the Violet Moon |
| Cape Dragon Spine | りゅうの しっぽ | the Dragon's Tail |
| Alisa III | アリサ3せい | the Alisa III (plain letters in dialogue) |
| Palm / Neo Palm / Algo | パルマ / ネオパルマ / アルゴル | Palma / Neo Palma / Algol |
| Dark Force | ダークファルス | Dark Falz |
| the Engine Room | エンジンルーム | the Engine Room |

Peoples: ライアの たみ / いちぞく = Laia's people, Laia's clan, the Laians;
オラキオの たみ = Orakio's people, the Orakians.

## Techniques

The JP names are not the Foi/Zan family of the other games for most of the
list; the US release renamed them to match PS II/IV. **Decided: the JP
names** - Foie, Zan, Gravt, Barta, Sun Force, Star Force, Moon Force, Sea
Force, Rising, Noon, Fall, Night, Law, Unbalance, Balance, Chaos, Megid,
Grantz (all inside 72 px; the Techs screen repeats them in `menus`).

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
US called them Melee, Order, Heal, Time - now Attack / Balance / Recovery /
Time Tech. The distributor NPC is マスター, "the Master".

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

The US item names were cut to nine cells. Every item window draws the
proportional face now; the tightest is the battle item list at nine cells,
so the budget is **72 px** (`proofread.html` measures it). **Decided: the JP
names, in full** (`work/script.json`, `items`): Antipoison, Star / Moon
Atomizer, Exa Ocarina; Soldier's / Knight's / Ceramic / Laser / Laconia /
Emperor / Planar / Orakio's / Nei Sword; the ラコニア metal is "Laconia"
throughout (its "Laconian" form pushes Laconia Bandana past 72 px); the
プロテクタ series keeps "Protector" (Ceramic Guard is セラミックガード in the JP),
and where a full name would pass 72 px the user's rule applies - first drop
the space, then an unpronounced letter: MaximaProtector (70 px), Laconia
Protectr (71 px; the letter alone suffices, so the space stays); フィブリラ is
Fibrilla; エーメル is the German Ärmel (sleeve), with Ä/ä added to the face;
"Grenade Launcher" (76 px) became "Grenade Gun"; せいきしのつるぎ (holy
knight's sword, 75 px) "Paladin Sword"; the two eclipse pieces are Eclipse
Armor (にっしょく) and Eclipse Robe (げっしょく). Key items: Forest
Sapphire, Moon Stone, Moon Tear, Dragon's Tear, Snow Crystal, Twins' Ruby,
Power Topaz, Mystery Star, Marine / Submarine / Sky Parts, Laia Pendant. The
legendary weapons as the sages name them: Orakio's Sword, the Miun Claw, the
Siren Shot, Laia's Bow, the Lune Slicer.

## Enemies

Mostly different names in the JP (Glop = ジェリー Jelly, the Grinder family
= バズール, Clops = ルーテラ, Dogbot = ヘルアーマー Hell Armour, Amazon =
ナスカ). **Decided: the JP names**, translated where they are words (Jelly,
Butterfly, Rappy, Death Lizard, Hand Walker, Hell Armor, Ghost / Hero / Grief
Tree, Dragon King...) and transliterated where they are not (Fial, Cham,
Sheela, Naruga, Wezal, Bazul, Lutera, Nasca, Astilus...). バスタード is
rendered Bustard. The full list is in `work/script.json` (`enemies`); every
name is inside the 75 px of the battle box's group line.

## Places

To be read from the script: the JP dialogue uses different names for the
kingdoms (リーク for Landen's kingdom, サテライト for Azura, "the desert
dome" for Aridia, ...). `work/dialogue.json` has them in context.

## Text conventions

* `{PAGE}` scrolls one line; keep each page to one line after the first
  `{BR}`.
* Speaker labels: the US convention `KEIN "..."` where the JP has a label
  (`ケイン 「...」`); bare `「...」` lines keep their quotation marks without a
  label. `-sama` becomes Lord / Lady / Prince / Queen as the rank allows.
* The three lines the US emptied in Landen (`loc_261F8`, `loc_261FC`,
  `loc_26200`, reached with flag $16) and the other header-only entries carry
  their JP text again (see `docs/pipeline.md`).
* Numbers inserted by the engine (`{NUM:nn}`) are drawn with the digit
  glyphs; budget them as three or four digits.
