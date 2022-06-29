# Chemistry Utils

Three tools are provided in this folder for now:

- Chemical calculator
- Chemical equation balancer (deprecated)
- Dimensional analysis calculator (deprecated)

The goal is, that the chemical calculator will integrate the functionality of the
chemical equation balancer and DA calculator. However, due to limitations of my
ability, I shall start implementation step by step. So we will have to use that two
deprecated stuff for now.

## Syntax

### Lexical grammar

```text
STR         -> ( "s" )? "\"" (not "\"" or "\"" with preceding "\\")* "\"" | ( "s" )? "doc" (any string sequence not including "done")+ "done"
FORMULA     -> compound ( "^" "{" NUMBER ( "+" | "-" ) "}" )? | compound ( "^" NUMBER ( "+" | "-" ) )?;
compound    -> ( ( ELEMENT | "(" ELEMENT ")" ) ( "_" "{" (any char that is not "}") "}" | "_" NUMBER | NUMBER )? )+;
PATH        ->  (path_car)* ( "\" (path_char " ")* )+ | "|" ( any char that is not "|" ) ( "\" ( any char that is not "|" )* )+ "|";
path_char   -> any char that is not "<>/|?*(){}" and not space
UNIT        -> "m" | "in" | "ft" | "yd" | "mi" | "acre" | "L" ... See pint default units.;
PLURAL      -> "s" | "es" | "ves" | "ies";
NUMBER      -> DIGIT+ ( "." DIGIT+ )? ( ( "e" | "E" ) DIGIT )?;
IDENTIFIER  -> ALPHA ( ALPHA | DIGIT )*;
ALPHA       -> "_" | "a" ... "z" | "A" ... "Z" | U+0000 ... U+10FFFF;
DIGIT       -> "0" ... "9";
ELEMENT     -> "H"|"He"|"Li"|"Be"|"B"|"C"|"N"|"O"|"F"|"Ne"|"Na"|"Mg"|"Al"|"Si"|"P"|"S"|"Cl"|"Ar"|"K"|"Ca"|"Sc"|"Ti"|"V"|"Cr"|"Mn"|"Fe"|"Co"|"Ni"|"Cu"|"Zn"|"Ga"|"Ge"|"As"|"Se"|"Br"|"Kr"|"Rb"|"Sr"|"Y"|"Zr"|"Nb"|"Mo"|"Tc"|"Ru"|"Rh"|"Pd"|"Ag"|"Cd"|"In"|"Sn"|"Sb"|"Te"|"I"|"Xe"|"Cs"|"Ba"|"La"|"Ce"|"Pr"|"Nd"|"Pm"|"Sm"|"Eu"|"Gd"|"Tb"|"Dy"|"Ho"|"Er"|"Tm"|"Yb"|"Lu"|"Hf"|"Ta"|"W"|"Re"|"Os"|"Ir"|"Pt"|"Au"|"Hg"|"Tl"|"Pb"|"Bi"|"Po"|"At"|"Rn"|"Fr"|"Ra"|"Ac"|"Th"|"Pa"|"U"|"Np"|"Pu"|"Am"|"Cm"|"Bk"|"Cf"|"Es"|"Fm"|"Md"|"No"|"Lr"|"Rf"|"Db"|"Sg"|"Bh"|"Hs"|"Mt"|"Ds"|"Rg"|"Cn"|"Nh"|"Fl"|"Mc"|"Lv"|"Ts"|"Og";
```

### Expression

```text
expr        -> interval;
write       -> interval -> PATH;
interval    -> assign "..." assign;
assign      -> identifier '=' expr;
ternary     -> "(" expr ")" "?" expr ":" expr 
or          -> and ( "|" and )*;
and         -> eq ( "&" eq )*;
eq          -> cp ( ("!=" | "==") cp )*;
cp          -> term ( ( ">" | ">=" | "<" | "<=" ) term)*;
term        -> factor ( ( "-" | "+" ) factor )*;
factor      -> unary ( ( "/" | "*" | "%" ) unary | ( reactions )?  ( "->"  ( UNIT | formula ) ) )*;
unary       -> ("!" | "-" | "+" | "~" ) unary | exp;
exp         -> call ( "**" | "^" ) "{" expr "}" | call ( "**" | "^" ) ( call );
call        -> primary ( "(" content? ")" ) | "." IDENTIFIER )*;
primary     -> IDENTIFIER | "pass" | "fail" | "(" expr ")" | "na" | STR | PATH | quantity;

identifier  -> IDENTIFIER | "`" IDENTIFIER "`"
reactions   -> ":" reaction ( "," reaction )* ":"
reaction    -> FORMULA  ( "+"  formula )* "->"  FORMULA ( "+" formula )*
quantity    -> primary ( unit )? ( formula )?;
content     -> expr ( "," expr )*;
unit        -> unit ( "/" | "*" ) UNIT ( "^" )? NUMBER  PLURAL? | UNIT PLURAL?;
```

### Statement

It is weird to call them statements. Since this is a super cow power (sorry `apt`) calculator,
all the statements are evaluated and have a return value. But we got to stop evaluation
of expression somewhere, so statements are still preserved.

All the statements, if not followed by a newline, can be written as oneliner. We allow
you to write assignment expressions inside this oneliner, and it will declare/define
variables in a separate lexica scope of the statement.

For work, the last line of statements will be automatically submitted (Nobody can write homework
but forgot to submit!), if you do not explicitly put a submit statement.

```text
stmt        ->  exam | redo | during | work | submit;
exam        -> "exam" expr SEP block ( "makeup" expr ( SEP block | expr ) )* ( "fail" SEP block )? SEP | "exam" expr ( "makeup" expr expr )* ( "fail" expr )?; 
redo        -> "redo" IDENTIFIER "of" interval ( SEP block | expr ) SEP;
during      -> "during" expr ( SEP block | expr ) SEP;
work        -> "work" IDENTIFIER "(" parameters? ")" ( SEP block | expr ) SEP;
submit      -> "submit" expr SEP;

parameters  -> IDENTIFIER ( "," IDENTIFIER )*;
block       -> INDENT stmt* DEDENT;

SEP         -> \n;
INDENT      -> ( "\t" | " " )*;
```

### Specification

- In this implementation, the recursive descent parser shall parse any expression that can
  be generated from the first production `expression -> interval`.
- A number without a unit is considered a scalar, which would only change the
  quantity in the expression (if any), but not their unit. However, if multiple units
  are found, dimensional analysis is running with `Graph`.
- Chemical formulas are treated as a `quantity` with `g/mol` as the unit. However, one could
  use a different aspect of the chemical formula to calculate, e.g., the sum of
  electronegativity, the sum of atomic numbers, etc.

## Execution

- This is an interpreter that evaluates/generate result through iteration of the tree,
  a.k.a., syntax-directed generation.
