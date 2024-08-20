package spoon_test;

import spoon.processing.AbstractProcessor;
import spoon.reflect.code.CtCodeSnippetStatement;
import spoon.reflect.declaration.CtClass;
import spoon.reflect.declaration.CtExecutable;

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
public class LogProcessor extends AbstractProcessor<CtExecutable> {

	@Override
	public void process(CtExecutable element) {
		CtCodeSnippetStatement snippet = getFactory().Core().createCodeSnippetStatement();
        String method_name = element.getSignature();
		// Snippet which contains the log.
		final String value = String.format("try {\njava.io.BufferedWriter bufferedWriter = new java.io.BufferedWriter(new java.io.FileWriter(\"call.txt\", true));\nbufferedWriter.append(\""+method_name+"\\n\");\nbufferedWriter.close();\n} catch (java.io.IOException eWriter) {\neWriter.printStackTrace();\n}");
        snippet.setValue(value);

		// Inserts the snippet at the beginning of the method body.
		if (element.getBody() != null) {
			element.getBody().insertBegin(snippet);
		}
	}
}
