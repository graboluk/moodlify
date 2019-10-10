# moodlify - python script and latex template for facilitating creation of maths moodle quizzes

## What problem does it solve?

I wanted to be able to create a moodle quiz quickly from a latex file. It should be possible to
reuse the latex source to create a pdf and html with the quiz, without any modification to the latex source (useful for accessibility reasons).

## Usage

Create a latex file similar to example.tex. In particular it should include moodle.sty via 
```
\input{moodle.sty}
```
in the preamble. If creating a pdf file with pdflatex, there is an option to indicate correct answers, by using 
```
\showinfo
```
in the preamble.

To create a moodle file with questions, run e.g.
```
python3 moodlify.py --in source.tex --out moodle_questions.txt
```
In moodle, moodle_questions.txt can be imported to the question bank (use GIFT when choosing input format)

## Bugs

There are plenty including wery rough corner cutting. I'll fix bugs quickly only when I need for my own use cases, but bug reports still welcome (fixes even more welcome).

## License

Licensed under GPL3. But in case you would like to contribute I require all contribution to be dual licensed MPL2/GPL3, so that it's easy to change the license to another free software license if ever need be.
