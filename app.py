from lxml import etree
from xmldiff import main, formatting 
from flask import request, url_for, Flask
import base64
import lxml.etree


XSLT = u'''<?xml version="1.0"?>

<xsl:stylesheet version="1.0"
    xmlns:diff="http://namespaces.shoobx.com/diff"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    
    <xsl:template name="mark-diff-insert">
        
        <ins class="diff-insert">
        
            <xsl:apply-templates/>
        </ins>
        
    </xsl:template>

    <xsl:template name="mark-diff-delete">
        <del class="diff-del">
            <xsl:apply-templates/>
        </del>
    </xsl:template>

    <xsl:template name="mark-diff-insert-formatting">
        <span class="diff-insert-formatting" style="color:red;">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template name="mark-diff-delete-formatting">
        <span class="diff-delete-formatting">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <!-- `diff:insert` and `diff:delete` elements are only placed around
        text. -->
   
    <xsl:template match="diff:insert">
    
            <xsl:apply-templates  />
    
    </xsl:template>

    <xsl:template match="*">
    <span style="color:green;">
            <xsl:element name="{local-name()}">
            <xsl:attribute name="style" class="insert">color:red;</xsl:attribute>        
            <xsl:apply-templates  />
        </xsl:element>
    </span>        
    </xsl:template>

    <xsl:template match="*[@diff:insert]">    
        <span style="color:green;">    
            <xsl:element name="{local-name()}">
                <xsl:apply-templates  />
            </xsl:element>
        </span>        
    </xsl:template>
   
    <xsl:template match="*[@diff:delete]">
        <span style="color:red;">    
            <xsl:element name="{local-name()}">
                <xsl:apply-templates  />
            </xsl:element>
        </span>   
    </xsl:template>

    <!-- If any major paragraph element is inside a diff tag, put the markup
        around the entire paragraph. -->
    <xsl:template match="p|h1|h2|h3|h4|h5|h6">
        <xsl:choose>
            <xsl:when test="ancestor-or-self::*[@diff:insert]">
                
                <xsl:copy>
                    <xsl:call-template name="mark-diff-insert" />
                </xsl:copy>
            </xsl:when>
            <xsl:when test="ancestor-or-self::*[@diff:delete]">
                <xsl:copy>
                    <xsl:call-template name="mark-diff-delete" />
                </xsl:copy>
            </xsl:when>
            <xsl:otherwise>
                <xsl:copy>
                    <xsl:apply-templates/>
                </xsl:copy>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- Put diff markup in marked paragraph formatting tags. -->
    <xsl:template match="span|b|i|u|strike|sub|sup">
        <xsl:choose>
            <xsl:when test="@diff:insert">
            
                <xsl:copy>
                    <xsl:call-template name="mark-diff-insert" />
                </xsl:copy>
            
            </xsl:when>
            <xsl:when test="@diff:delete">
                <xsl:copy>
                    <xsl:call-template name="mark-diff-delete" />
                </xsl:copy>
            </xsl:when>
            <xsl:when test="@diff:insert-formatting">
                <xsl:copy>
                    <xsl:call-template name="mark-diff-insert-formatting" />
                </xsl:copy>
            </xsl:when>
            <xsl:when test="@diff:delete-formatting">
                <xsl:copy>
                    <xsl:call-template name="mark-diff-delete-formatting" />
                </xsl:copy>
            </xsl:when>
            <xsl:otherwise>
                <xsl:copy>
                    <xsl:apply-templates/>
                </xsl:copy>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- Put diff markup into pseudo-paragraph tags, if they act as paragraph. -->
    <xsl:template match="li|th|td">
        <xsl:variable name="localParas" select="para|h1|h2|h3|h4|h5|h6" />
        <xsl:choose>
            <xsl:when test="not($localParas) and ancestor-or-self::*[@diff:insert]">
                <xsl:copy>
                    <para>
                        <xsl:call-template name="mark-diff-insert" />
                    </para>
                </xsl:copy>
            </xsl:when>
            <xsl:when test="not($localParas) and ancestor-or-self::*[@diff:delete]">
                <xsl:copy>
                    <para>
                        <xsl:call-template name="mark-diff-delete" />
                    </para>
                </xsl:copy>
            </xsl:when>
            <xsl:otherwise>
                <xsl:copy>
                    <xsl:apply-templates/>
                </xsl:copy>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>


    <!-- =====[ Boilerplate ]=============================================== -->

    <!-- Remove all processing information -->
    <xsl:template match="//processing-instruction()" />

    <!-- Catch all with Identity Recursion -->
    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>

    <!-- Main rule for whole document -->
    <xsl:template match="/">
        <xsl:apply-templates/>
    </xsl:template>

</xsl:stylesheet>
'''
XSLT_TEMPLATE = lxml.etree.fromstring(XSLT)
class HTMLFormatter(formatting.XMLFormatter):
    def render(self, result):
        transform = lxml.etree.XSLT(XSLT_TEMPLATE)
        result = transform(result)
        return super(HTMLFormatter, self).render(result)

app = Flask(__name__)

@app.route("/CompareXML/", methods=['POST'])
def compare_xml():
    json_data = request.json
    base64_file1 = json_data["FILE1"]["base64"]
    base64_file2 = json_data["FILE2"]["base64"]
    mimetype_file1 = json_data["FILE1"]["mimetype"]
    mimetype_file2 = json_data["FILE2"]["mimetype"]
    if request.method == 'POST':
        if json_data: 
            #if data exists in the request at all
            if base64_file1 and base64_file2 and mimetype_file1 and mimetype_file2:
                
                #data exists properly in the request
                if mimetype_file1 == "text/xml" and mimetype_file2 == "text/xml":
                        formatter = HTMLFormatter(text_tags=('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'))
                        diff = main.diff_texts(base64.b64decode(base64_file1),base64.b64decode(base64_file2),formatter=formatter)
                        str_diff = str(diff)
                        str_diff = str_diff.replace('<','&lt;')
                        str_diff = str_diff.replace('>','&gt;')
                        str_diff = str_diff.replace('</','<br />&lt;/')
                        str_diff = str_diff.replace('&lt;span style="color:green;"&gt;','<span style="color:green;">')
                        str_diff = str_diff.replace('&lt;span style="color:red;"&gt;','<span style="color:red;">')
                        str_diff = str_diff.replace('&lt;/span&gt;','</span>')
                        str_diff = str_diff.replace('\n','<br />')
                        str_diff = str_diff.replace(' xmlns:diff="http://namespaces.shoobx.com/diff"','')
                        f = open("output.html","w")
                        f.write(str_diff)
                        print("COMPLETE")
                        return str_diff
                else:
                    print("File 1 mimetype is not supported")
                    return None
            return "Bad Request."
    else:
        return "Method Not Supported."

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=8422,debug=False)

