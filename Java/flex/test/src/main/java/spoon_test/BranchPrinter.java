package spoon_test;

import spoon.processing.AbstractProcessor;
import spoon.reflect.code.CtCodeSnippetStatement;
import spoon.reflect.declaration.CtClass;
import spoon.reflect.declaration.CtExecutable;
import spoon.reflect.code.CtBlock;
import spoon.reflect.code.CtStatement;
import spoon.reflect.code.CtIf;
import spoon.reflect.declaration.CtElement;
import java.util.List;
import java.util.ArrayList;

/**
 * Example of tracing
 *
 * class A{
 *   void m(Object o} { ...(method body) .... }
 * }
 *
 * is transformed into
 *
 *  void m(Object o} {
 *      System.out.println("enter in method m from class A");
 *      // rest of the method body
 *  }
 * Use with
 * $ java -jar spoon.jar -i src/main/java -o spooned -p fr.inria.gforge.spoon.transformation.autologging.LogProcessor
 *
 * Of with https://github.com/SpoonLabs/spoon-maven-plugin
 *
 */
public class BranchPrinter extends AbstractProcessor<CtElement> {
    @Override
    public boolean isToBeProcessed(CtElement element) {
		return element instanceof CtIf;
	}
	@Override
	public void process(CtElement stmt) {

		// Snippet which contains the log.
        CtCodeSnippetStatement snippet;
        CtCodeSnippetStatement snippet_true;
        CtCodeSnippetStatement snippet_false;
                if (stmt instanceof CtIf) {
                    CtIf s = (CtIf) stmt;
                    CtElement s_new = getFactory().Core().clone(s);

            		snippet = getFactory().Core().createCodeSnippetStatement();
            		snippet_true = getFactory().Core().createCodeSnippetStatement();
            		snippet_false = getFactory().Core().createCodeSnippetStatement();
		            String value = String.format("try {\njava.io.BufferedWriter bufferedWriter = new java.io.BufferedWriter(new java.io.FileWriter(\"branch.txt\", true));\nbufferedWriter.append(\""+s.getPosition().toString()+"\\n\");\nbufferedWriter.close();\n} catch (java.io.IOException eWriter) {\neWriter.printStackTrace();\n}");
		            String value_true = String.format("try {\njava.io.BufferedWriter bufferedWriter = new java.io.BufferedWriter(new java.io.FileWriter(\"branch.txt\", true));\nbufferedWriter.append(\""+"true"+"\\n\");\nbufferedWriter.close();\n} catch (java.io.IOException eWriter) {\neWriter.printStackTrace();\n}");
		            String value_false = String.format("try {\njava.io.BufferedWriter bufferedWriter = new java.io.BufferedWriter(new java.io.FileWriter(\"branch.txt\", true));\nbufferedWriter.append(\""+"false"+"\\n\");\nbufferedWriter.close();\n} catch (java.io.IOException eWriter) {\neWriter.printStackTrace();\n}");
                    snippet.setValue(value);
                    snippet_true.setValue(value_true);
                    snippet_false.setValue(value_false);
                    //System.out.println(s.getPosition().toString());
                    //ArrayList<CtElement> s_list = new ArrayList<CtElement>();
                    //s_list.add(snippet);
                    //s_list.add(s_new);
                    //s.replace(s_list);
                    //stmtList_new.add(snippet);
                    s.insertBefore(snippet);

                    CtBlock thenBlock = s.getThenStatement();
                    CtBlock elseBlock = s.getElseStatement();
                    if (thenBlock != null) {
                        thenBlock.insertBegin(snippet_true);
                    } else {
                        s.setThenStatement(snippet_true);
                    }
                    if (elseBlock != null) {
                        elseBlock.insertBegin(snippet_false);
                    } else {
                        s.setElseStatement(snippet_false);
                    }
                }
                //stmtList_new.add(s);
            //body.setStatements(stmtList_new);
		// Inserts the snippet at the beginning of the method body.
	}
}
