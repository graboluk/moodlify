import re, copy, random
txt_example = ""

macros = [] #macros[k] shoud be macros with k arguments, no optarg support for now
macros.append([])
macros.append(['\\section', '\\subsection'])
env_opt = ['enumerate']

def randomword(length):
   return ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(length))


def is_uncommented(txt,pos,comment_smb):
    if comment_smb == None: 
        return True
    m = txt[:pos].split("\n")[-1]
    if m.find(comment_smb) >= 0: return False
    else: return True

def find_closing_bracket(txt, pos=None, op='(',cl=')', comment_smb = None):
    search_term = '(' + re.escape(op) + '|' + re.escape(cl) + ')'

    if pos==None: 
        m = re.search('^[^%\n]*?'+search_term, txt,flags=re.MULTILINE)
        if not m:
            raise SyntaxWarning('There are no ', op, ' nor ', cl, ' parens in ', txt) 
        if m.group(1) == cl:
            raise SyntaxError('The first paren in ', txt, ' is a closing paren ', cl)
        if m.group(1) == op:
            pos = m.start(1)

    if not re.match(re.escape(op), txt[pos:]):
        raise AssertionError("Expected to find ", op, " at ", pos, " in ", txt)
     
    count = 1
    search_pos=pos+1
    while count > 0:
        m = re.search(search_term, txt[search_pos:])
        if not m:
            raise SyntaxError("No matching paren ", cl, " for ", op ," at ", pos, " in ", txt) 
        if m.group(1) == op and is_uncommented(txt,m.start(1),comment_smb):
            count += 1
        if m.group(1) == cl and is_uncommented(txt,m.start(1),comment_smb):
            count -= 1
        if count == 0:
            return search_pos + m.start(1), search_pos +m.end(1)
        search_pos += m.end(1)


def find_arg_at(txt,pos = 0): 
    #~ returns arg, first position outside of arg-related latex
    m = re.match("[ \t]*?\n?[ \t]*?(\S)", txt[pos:])
    if not m: 
        raise SyntaxError("No LaTeX arguments in ", txt, " at ", pos)

    if not m.group(1) in ['{','\\']: 
        return m.group(1), pos + m.end(1)

    if m.group(1) == '{':
        closing_start, closing_end= find_closing_bracket(txt,pos+m.start(1), '{','}')
        return txt[pos+m.start(1)+1:closing_start], closing_end

    if m.group(1) == '\\':
        m = re.match("[ \t]*?\n?[ \t]*?(\\\\[a-zA-Z\*]*)", txt[pos:])
        return m.group(1), pos + m.end(1)


def find_optarg_at(txt, pos=0):
    #~ returns arg, first position outside of arg-related latex
    m = re.match("[ \t]*?\n?[ \t]*?\[(.*?)\]", txt[pos:], flags=re.DOTALL + re.MULTILINE)
    if not m: return None, pos
    else: return m.group(1), pos+m.end(1)+1

def txt2nodes(txt,macros=macros):
    # ~ print(txt)
    s = '|'.join([re.escape(x) for x in macros[0]+macros[1] + ['\\begin']])
    nodes = []
    start_from = 0
    force_text_node=True
    while(start_from < len(txt)):
        m = re.search('^[^%\n]*?(' + s + ')[^a-zA-Z\*]', txt[start_from:], flags= re.MULTILINE)

        if not m: 
            nodes.append({'node_type': 'text', 'content': txt[start_from:], 'real_name':[]})
            return nodes

        if m.start(1) > 0:
            nodes.append({'node_type': 'text', 'content': txt[start_from:start_from+m.start(1)]}) 
            force_text_node = False

        if force_text_node:
            nodes.append({'node_type': 'text', 'content': ''}) 
            force_text_node = False
       
        what = m.group(1)

        if what in macros[0]:
            nodes.append({'node_type': 'macro', 'macro_name': what[1:], 'arg': None})
            start_from += m.end(1)
            force_text_node = True

        if what in macros[1]:
            arg, endpos = find_arg_at(txt, start_from + m.end(1))
            nodes.append({'node_type': 'macro', 'macro_name': what[1:], 'arg': arg})
            start_from = endpos
            force_text_node = True
            #~ print(arg, endpos)
    
        if what == '\\begin':
            env_name, endpos = find_arg_at(txt, start_from + m.end(1))
            # below -1 is because we want find_closing_bracket to consider from backslash.
            cl_start, cl_end = find_closing_bracket(txt, pos = start_from + m.start(1), op='\\begin{'+env_name+'}', cl='\\end{'+env_name+'}')
            nodes.append({'node_type': 'env', 'env_name': env_name, 'content': txt2nodes(txt[endpos:cl_start],macros=macros)})
            start_from = cl_end
            force_text_node = True


    if len(nodes) == 0 or not nodes[-1]["node_type"] == 'text':
        nodes.append({'node_type': 'text', 'content': ''}) 
        
    return nodes

txt = """\\documentclass[sdfsdf]{article}
\\usepackage[utf8]{inputenc}
\\usepackage[american]{babel}

\\title{Łała}
\\author{Dupa}
\\date{\today}

\\begin{document}
\\maketitle
Lala
\\end{document}
"""

txt2 = '%go to line 433\n\\documentclass [12pt,a4paper] {amsart}\n\n\\usepackage{amsmath, amsfonts, xifthen, late'


c = {"\\documentclass": [1,1],
    "\\usepackage": [1,1],
    "\\title": [0,1],
    "\\author": [0,1],
    "\\date": [0,1],
    }

def what_is_first_macro(txt):
    # returns [a, pos, b,[c,d]], where a is macro in the form "\\section", etc
    # b is optional argument or None
    # [c.d] is list of normal arguments or None
    # pos is end of macro, so position of first sign outside.
    # if macro name is not in c then return just [a,pos]

    m = re.search('^[^%\n]*?(\\\\[a-zA-Z\*]*)[^a-zA-Z\*]', txt, flags= re.MULTILINE)
    if not m: return None
    macro_name = m.group(1)
    macro_name_end = m.end(1)
    if not macro_name in c: 
        return [macro_name, macro_name_end]
    if c[macro_name][0]:
        opt_arg, opt_arg_end = find_optarg_at(txt, macro_name_end)
        end_so_far = opt_arg_end
    else:
        opt_arg = None
        end_so_far = macro_name_end
    
    if c[macro_name][1]:
        normal_args = []
        for n in range(c[macro_name][1]):
            arg, end_so_far = find_arg_at(txt, end_so_far)
            normal_args.append(arg)

    return [macro_name, end_so_far,opt_arg,normal_args]

def get_all_macros(txt):
    ntxt = txt
    ret = []
    end_so_far = 0 
    while True:
        try:
            name, end_so_far = what_is_first_macro(ntxt)[:2]
        except:
            return ret

        if not name in ret: ret.append(name)
        ntxt = ntxt[end_so_far:]

def txt2preamble(txt):
    end_so_far = 0
    ret = {}
    ret["documentclass"] = None
    ret["packages"] = []
    ret["title"] = None
    ret['author'] = None
    ret['date'] = None
    try: 
        x = what_is_first_macro(txt[end_so_far:])
        assert x[0] == '\\documentclass'
    except (SyntaxError, SyntaxWarning, AssertionError):
        ret['preamble_edit'] =txt[end_so_far:]
        return ret
    end_so_far += x[1]

    ret["documentclass"] = {'opt_arg':x[2], 'arg': x[3][0]}

    try:
        x = what_is_first_macro(txt[end_so_far:])
        assert x[0] in ['\\usepackage', '\\title', '\\author', '\\date']
    except (SyntaxError, SyntaxWarning, AssertionError):
        ret['preamble_edit'] = txt[end_so_far:]
        return ret
    end_so_far += x[1]

    while x[0] == '\\usepackage':
        ret["packages"].append({'opt_arg':x[2], 'arg':x[3][0]})
        try:
            x = what_is_first_macro(txt[end_so_far:])
            assert x[0] in ['\\usepackage', '\\title', '\\author', '\\date']
        except (SyntaxError, SyntaxWarning, AssertionError):
            ret['preamble_edit'] = txt[end_so_far:]
            return ret
        end_so_far += x[1]
        #~ print(x[0]) 

    ret[x[0][1:]] = x[3][0]

    while True:
        try:
            x = what_is_first_macro(txt[end_so_far:])
            assert x[0] in ['\\title', '\\author', '\\date']
            assert type(x[3][0]) == str
        except:
            ret['preamble_edit'] = txt[end_so_far:]
            return ret
        end_so_far += x[1]
        ret[x[0][1:]] = x[3][0]

def split_file(txt):
    # should return three parts: preamble, whatever goes between begin doc and end doc, and whatever is after.
    # if this is not possible then either preamble and junk, or only junk in no \begin{document}
    m = re.search('^[^%\n]*?(\\\\begin{document})',txt,re.MULTILINE)
    if not m: raise SyntaxError("I didn't find \\begin{document}") 
    op1= m.start(1)
    op2= m.end(1)
    try:
        cl1, cl2 = find_closing_bracket(txt, pos=op1, op='\\begin{document}', cl='\\end{document}', comment_smb = '%')
    except (SyntaxError, SyntaxWarning, AssertionError):
        raise SyntaxError("I didn't find a correct \\end{document}. There is either no uncommented \\end{document} or too many \\end{document} statements")
    return txt[:op1], txt[op2:cl1], txt[cl2:]


def normalize_begin(txt):
# normalization of document part:
#~ Make sure there are no spaces in \begin{env} and \end{env}, because these are used as opening and closing parens
    ntxt = re.sub('\\\\begin[ \t]*\n?[ \t]*{', '\\\\begin{', txt)
    ntxt = re.sub('\\\\end[ \t]*\n?[ \t]*{', '\\\\end{', ntxt)
    return ntxt

def remove_comments(txt):
    token =  randomword(10)
    ntxt = re.sub('\\\\\\\\',token,txt)
    ntxt = re.sub('([^\\\\])(%.*)',"\\1", ntxt)
    ntxt = re.sub('^%.*',"", ntxt)
    ntxt = re.sub(token, '\\\\\\\\',ntxt)
    return ntxt


def load_tex(t):
    txt = normalize_begin(t)
    try:
        preA, preB, preC = split_file(txt)
    except:
        return {'preamble':None,'nodes': None,'junk': txt}
    ret = {}
    ret["preamble"] = txt2preamble(preA)
    ret["nodes"] = txt2nodes(preB)
    ret["junk"] = preC
    return ret

   
def load_file(f):
    with open(f,'r') as myfile:
        txt = myfile.read()
    return load_tex(txt)

def serialize_node(n, nltoken):
        if n['node_type'] == 'text': return n['content']
        if n['node_type'] == 'macro':
            return nltoken+'\\'+n['macro_name'] + '{' + n['arg'] + '}'+nltoken
        if n['node_type'] == 'env':
            output = nltoken+'\\begin{'+ n['env_name'] + '}'
            for x in n['content']:
                output +=  serialize_node(x,nltoken)
            output += '\\end{'+ n['env_name'] + '}'+nltoken
            return output
  

def serialize(f):
    nltoken= randomword(10)
    output = ""
    a = f["preamble"]
    b = f["nodes"]
    c = f["junk"]
    if a:
        if a["documentclass"]:
            output += '\\documentclass['+ a["documentclass"]['opt_arg']+ ']{' + a["documentclass"]['arg'] +  '}\n'
        if a["packages"]:
            for p in a["packages"]:
                print(p)
                output += '\\usepackage[' + p['opt_arg'] + ']{' + p['arg'] + '}\n'
        for x in ["title", "author", "date"]:
            if a[x]:
                output += '\\' + x + '{' + a[x]['arg'] + '}'
                if not x == 'date': output +='\n'

        output +='\n' if (not output or not output[-1] == '\n') and (not a["preamble_edit"] or not a["preamble_edit"][0] == '\n') else ''
        output += a["preamble_edit"] 

    if b:
        output += '\n' if not output[-1] == '\n' else '' 
        output += '\\begin{document}'
        #~ potential_newline = True
        for n in b:
            #~ if n['node_type'] == 'env' or n['node_type']=='macro' and n['macro_name'] in ['subsection','section'] or potential_newline:
                #~ output +='\n' if not output[-1] == '\n' and not serialize_node(n)[0] == '\n' else ''
                #~ potential_newline = False
            output += serialize_node(n, nltoken)
            #~ if n['node_type'] == 'env' or n['node_type']=='macro' and n['macro_name'] in ['subsection','section']:
                #~ potential_newline = True

        if not output[-1] =='\n':  
            output += '\n'
        output += '\\end{document}'

    if c:
        if not c[0]== '\n': output += '\n'
        output += c
        if not output[-1] =='\n':  
            output += '\n'

    output = re.sub(r'([^\n])'+nltoken+'([^\n])',r'\1\n\2',output,flags=re.MULTILINE) 
    output = re.sub(nltoken,'',output,flags=re.MULTILINE) 

    return output
