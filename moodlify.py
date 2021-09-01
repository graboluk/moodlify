#!/bin/python3
#! Copyrights Łukasz Grabowski

import yaml
import sys, os, re
import argparse, copy, datetime, subprocess
import latexio


def get_newcommands(txt): #returns dictionary of newcommands
    ntxt = txt
    ret = {}
    while(latexio.what_is_first_macro(ntxt)):
        macro,pos = latexio.what_is_first_macro(ntxt)[:2]
        if macro == "\\newcommand":
            old,pos = latexio.find_arg_at(ntxt,pos)
            new,pos = latexio.find_arg_at(ntxt,pos)
            ret[old] = new
        ntxt = ntxt[pos:]
    return ret

def initial_clean(tex):
    out = latexio.normalize_begin(tex)
    out = latexio.remove_comments(tex)
    return out

def apply_newcommand(old, new, txt):
    #naive version, should be a suitable re.sub:
    return txt.replace(old,new)
    

def apply_newcommands(newcommands, txt): # naivelyn apply them for as long as we can - this will work fine on a legal latex source, but will potentitally enter an infinte loop on an illegal latex source
    # ~ print(newcommands)
    ntxt = txt
    allmacros=latexio.get_all_macros(ntxt)
    relevant = [x for x in newcommands if x in allmacros]
    
    while relevant:
        for m in relevant:
            ntxt = apply_newcommand(m, newcommands[m],ntxt)

        allmacros=latexio.get_all_macros(ntxt)
        relevant = [x for x in newcommands if x in allmacros]
    return ntxt

def serialise_problem_content(nodes,nltoken, bracetokenl,bracetokenr,equaltoken,tildetoken,hashtoken,markdowntoken):

    ret = markdowntoken
    answers_started = False
    # ~ print(nodes)
    for m in nodes:
        if m["node_type"] == "macro" and m["macro_name"] in ["bad", "good"]:
            if not answers_started:
                ret = ret +bracetokenl
                # ~ print("not answers_started")
                answers_started = True
            ret = ret+nltoken + (tildetoken if m["macro_name"]=="bad" else equaltoken)
        elif m["node_type"] == "macro" and m["macro_name"] == "tutma":
            pass
        else: ret = ret + latexio.serialize_node(m,nltoken)
    ret = ret + nltoken + bracetokenr
    ret = ret.replace("\\{","\\lbrace")
    ret = ret.replace("\\}","\\rbrace")
    ret = ret.replace("{","\\{")
    ret = ret.replace("}","\\}")
    ret = ret.replace("~","\\~")
    ret = ret.replace("=","\\=")
    ret = ret.replace("#","\\#")
    #naive, should be sub which avoida escaped $:
    ret = ret.replace("$","$$")

    return ret


def moodlify(txt): #replace { with \{, etc.
    nodes = latexio.txt2nodes(txt,macros=[["\\good","\\bad"],["\\moodlecat","\\tutma"]])

    output = ""

    nltoken = latexio.randomword(10)
    bracetokenl = latexio.randomword(10)
    bracetokenr = latexio.randomword(10)
    equaltoken = latexio.randomword(10)
    tildetoken = latexio.randomword(10)
    hashtoken = latexio.randomword(10)
    markdowntoken = latexio.randomword(10)

    
    for m in nodes: 
        if m["node_type"] =="macro" and  m["macro_name"] == "moodlecat":
             output = output + nltoken+ "$CATEGORY:"+m["arg"]+nltoken

        if m["node_type"] == "env" and m["env_name"] == "problem":
            output = output + nltoken + serialise_problem_content(m["content"],nltoken,bracetokenl,bracetokenr,equaltoken,tildetoken,hashtoken,markdowntoken)+nltoken

    output = re.sub(r'([^\n])'+nltoken+'([^\n])',r'\1\n\2',output,flags=re.MULTILINE) 
    output = re.sub(nltoken,'',output,flags=re.MULTILINE) 


    output = re.sub('\s*'+bracetokenl+'\s*'," {",output, flags =re.MULTILINE)
    output = re.sub('\s*'+bracetokenr+'\s*',"\n}",output,flags=re.MULTILINE)
    output = re.sub('\s*'+tildetoken+'\s*',"\n~",output, flags=re.MULTILINE)
    output = re.sub('\s*'+equaltoken+'\s*',"\n=",output, flags=re.MULTILINE)
    output = re.sub('\s*'+hashtoken+'\s*',"#",output, flags=re.MULTILINE)
    output = re.sub('\s*'+markdowntoken+'\s*',"\n\n[markdown]",output, flags=re.MULTILINE)

    return output



def extract_moodle_content(txt):

    nodes = latexio.txt2nodes(txt,macros=[[],["\\moodlecat","\\tutma"]])

    mynodes = [m for m in nodes if (m["node_type"] =="macro" and  m["macro_name"] == "moodlecat") or (m["node_type"] == "env" and m["env_name"] == "problem")]

    # ~ for m in mynodes:
        # ~ if (m["node_type"] == "env" and m["env_name"] == "problem"):
            # ~ for 
    
            # ~ remove_tutma(m)



    output = ""
    nltoken = latexio.randomword(10)

    for n in mynodes:
        output = output + latexio.serialize_node(n,nltoken)

    output = re.sub(r'([^\n])'+nltoken+'([^\n])',r'\1\n\2',output,flags=re.MULTILINE) 
    output = re.sub(nltoken,'',output,flags=re.MULTILINE) 
    return output


parser = argparse.ArgumentParser()
parser.add_argument("--in", action="store",metavar="",dest = "input_path", required=True)
parser.add_argument("--out", action="store",metavar="",dest = "output_path", required=False)

args = parser.parse_args(sys.argv[1:])

with open(args.input_path, 'r') as infile:
    tex = infile.read()

tex = initial_clean(tex)

newcommands = get_newcommands(tex)

output = apply_newcommands(newcommands,latexio.split_file(tex)[1])

output = extract_moodle_content(output)

output = moodlify(output)


if not args.output_path is None:
    with open(args.output_path,'w') as outfile:
        outfile.write(output)
else:
    print(output)
