package spoon_test;
import spoon.reflect.declaration.*;
import spoon.*;
import spoon.reflect.code.CtExpression;
import spoon.reflect.code.CtIf;
import spoon.reflect.code.CtStatement;
import spoon.processing.AbstractProcessor;
import spoon.reflect.declaration.CtElement;
import spoon.reflect.declaration.CtClass;
import spoon.reflect.visitor.Filter;
import spoon.reflect.visitor.filter.TypeFilter;
import spoon.reflect.factory.Factory;
import spoon.reflect.factory.CodeFactory;
import spoon.reflect.visitor.PrettyPrinter;
import spoon.reflect.code.CtCodeSnippetStatement;
import spoon.reflect.cu.*;
import java.io.File;
import java.io.IOException;
import java.util.*;

import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
/**
 * Hello world!
 *
 */
/*
public class App 
{
    public static void main( String[] args )
    {
        System.out.println( "Hello World!" );
        CtClass l = Launcher.parseClass("class A { void m() { System.out.println(\"yeah\");} }");
        
    }
}
*/
public class App extends AbstractProcessor<CtElement> {
	@Override
	public boolean isToBeProcessed(CtElement candidate) {
		return candidate instanceof CtIf;
	}

    @Override
    public void process(CtElement candidate){
        return;
    }

	public void process2(CtElement candidate, CtExpression<Boolean> cond) {
		if (!(candidate instanceof CtIf)) {
			return;
		}
        CtIf op = (CtIf) candidate;
        // CodeFactory test = getFactory().Code();
        Launcher l = new Launcher();
        op.setCondition(cond);
	}

    public void conditionInstrumentor(String filePath, String targetPath, boolean bool, int location, String srcPath) {
        Launcher l = new Launcher();
        l.addInputResource(filePath);
        File f = new File(filePath);
        /*File fOrigin = new File(filePath+".origin");
        try {
            Files.copy(f.toPath(), fOrigin.toPath(), StandardCopyOption.REPLACE_EXISTING);
        } catch (IOException e) {
            e.printStackTrace();
            return;
        }*/
        l.setSourceOutputDirectory(srcPath);
        l.getEnvironment().setAutoImports(true);
        l.getEnvironment().setIgnoreDuplicateDeclarations(true);
        l.getEnvironment().setComplianceLevel(8);
        String[] classFile = {targetPath};
        l.getEnvironment().setSourceClasspath(classFile);
        l.buildModel();

        CtClass origClass = (CtClass) l.getFactory().Package().getRootPackage()
				.getElements(new TypeFilter(CtClass.class)).get(0);
        
        List<CtElement> elementsToBeMutated = origClass.getElements(new Filter<CtElement>() {

		    @Override
		    public boolean matches(CtElement arg0) {
			    return isToBeProcessed(arg0);
		    }
		});
        int i = 0;
        for (CtElement e : elementsToBeMutated) {
            if (e.getPosition().getLine() != location){
                continue;
            }
            System.out.println(i);
            CtElement op = l.getFactory().Core().clone(e);


            if (bool) {
                CtExpression<Boolean> true_cond = l.getFactory().Code().<Boolean>createCodeSnippetExpression("true");
                process2(op, true_cond);
            }
            else {
                CtExpression<Boolean> false_cond = l.getFactory().Code().<Boolean>createCodeSnippetExpression("false");
                process2(op, false_cond);
            }
            e.replace(op);
            CtClass klass = l.getFactory().Core()
					.clone(op.getParent(CtClass.class));
            i += 1;
        }
        // PrettyPrinter pp = l.createPrettyPrinter();
        // System.out.println(pp.getResult());
        l.prettyprint();
    }


    public void stmtDeleter(String filePath, String targetPath, int location) {
        Launcher l = new Launcher();
        l.addInputResource(filePath);
        File f = new File(filePath);
        /*File fOrigin = new File(filePath+".origin");
        try {
            Files.copy(f.toPath(), fOrigin.toPath(), StandardCopyOption.REPLACE_EXISTING);
        } catch (IOException e) {
            e.printStackTrace();
            return;
        }*/
        l.setSourceOutputDirectory(f.getParent());
        l.getEnvironment().setAutoImports(true);
        l.getEnvironment().setIgnoreDuplicateDeclarations(true);
        l.getEnvironment().setComplianceLevel(8);
        String[] classFile = {targetPath};
        l.getEnvironment().setSourceClasspath(classFile);
        l.buildModel();

        CtClass origClass = (CtClass) l.getFactory().Package().getRootPackage()
				.getElements(new TypeFilter(CtClass.class)).get(0);
        
        List<CtElement> elementsToBeMutated = origClass.getElements(new Filter<CtElement>() {

		    @Override
		    public boolean matches(CtElement arg0) {
			    return arg0 instanceof CtStatement;
		    }
		});
        int i = 0;
        for (CtElement e : elementsToBeMutated) {
            if (e.getPosition().getLine() != location){
                continue;
            }
            System.out.println(i);
            CtElement op = l.getFactory().Core().clone(e);

            /*
            if (bool) {
                CtExpression<Boolean> true_cond = l.getFactory().Code().<Boolean>createCodeSnippetExpression("true");
                process2(op, true_cond);
            }
            else {
                CtExpression<Boolean> false_cond = l.getFactory().Code().<Boolean>createCodeSnippetExpression("false");
                process2(op, false_cond);
            }
            e.replace(op);
            CtClass klass = l.getFactory().Core()
					.clone(op.getParent(CtClass.class));*/
            e.delete();
            i += 1;
        }
        // PrettyPrinter pp = l.createPrettyPrinter();
        // System.out.println(pp.getResult());
        l.prettyprint();
    }

    public void conditionRemover(String filePath, String targetPath, int location) {
        Launcher l = new Launcher();
        l.addInputResource(filePath);
        File f = new File(filePath);
        /*File fOrigin = new File(filePath+".origin");
        try {
            Files.copy(f.toPath(), fOrigin.toPath(), StandardCopyOption.REPLACE_EXISTING);
        } catch (IOException e) {
            e.printStackTrace();
            return;
        }*/
        l.setSourceOutputDirectory(f.getParent());
        l.getEnvironment().setAutoImports(true);
        l.getEnvironment().setIgnoreDuplicateDeclarations(true);
        l.getEnvironment().setComplianceLevel(8);
        String[] classFile = {targetPath};
        l.getEnvironment().setSourceClasspath(classFile);
        l.buildModel();

        CtClass origClass = (CtClass) l.getFactory().Package().getRootPackage()
				.getElements(new TypeFilter(CtClass.class)).get(0);
        
        List<CtElement> elementsToBeMutated = origClass.getElements(new Filter<CtElement>() {

		    @Override
		    public boolean matches(CtElement arg0) {
			    return isToBeProcessed(arg0);
		    }
		});
        int i = 0;
        for (CtElement e : elementsToBeMutated) {
            if (e.getPosition().getLine() != location){
                continue;
            }
            System.out.println(i);
            CtElement op = l.getFactory().Core().clone(e);

            /*
            if (bool) {
                CtExpression<Boolean> true_cond = l.getFactory().Code().<Boolean>createCodeSnippetExpression("true");
                process2(op, true_cond);
            }
            else {
                CtExpression<Boolean> false_cond = l.getFactory().Code().<Boolean>createCodeSnippetExpression("false");
                process2(op, false_cond);
            }
            e.replace(op);
            CtClass klass = l.getFactory().Core()
					.clone(op.getParent(CtClass.class));*/
            e.delete();
            i += 1;
        }
        // PrettyPrinter pp = l.createPrettyPrinter();
        // System.out.println(pp.getResult());
        l.prettyprint();
    }

    public void coverageInstrumentor(String filePath, String targetPath) {
        final String[] args = {
				//"-i", "/spoon_test/test/example/Foo1.java",
				//"-o", "/spoon_test/test/output/Foo1.java",
				"-p", "spoon_test.LogProcessor",
		};

		final Launcher launcher = new Launcher();
		launcher.setArgs(args);
        File f = new File(filePath);
        launcher.addInputResource(filePath);
        launcher.setSourceOutputDirectory(f.getParent());
        //launcher.setSourceOutputDirectory(filePath);
        launcher.getEnvironment().setAutoImports(true);
        launcher.getEnvironment().setIgnoreDuplicateDeclarations(true);
        launcher.getEnvironment().setComplianceLevel(8);
        String[] classFile = {targetPath};
        launcher.getEnvironment().setSourceClasspath(classFile);
		launcher.run();
        //launcher.getEnvironment().setAutoImports(false);
        //launcher.getEnvironment().setShouldCompile(true);
        launcher.prettyprint(); 
    }

    public void branchInstrumentor(String filePath, String targetPath, String srcPath) {
        final String[] args = {
				//"-i", "/spoon_test/test/example/Foo1.java",
				//"-o", "/spoon_test/test/output/Foo1.java",
				"-p", "spoon_test.BranchPrinter",
		};

		final Launcher launcher = new Launcher();
		launcher.setArgs(args);
        File f = new File(filePath);
        launcher.addInputResource(filePath);
        launcher.setSourceOutputDirectory(srcPath);
        //launcher.setSourceOutputDirectory(filePath);
        launcher.getEnvironment().setAutoImports(true);
        launcher.getEnvironment().setIgnoreDuplicateDeclarations(true);
        launcher.getEnvironment().setComplianceLevel(8);
        String[] classFile = {targetPath};
        launcher.getEnvironment().setSourceClasspath(classFile);
		launcher.run();
        //launcher.getEnvironment().setAutoImports(false);
        //launcher.getEnvironment().setShouldCompile(true);
        launcher.prettyprint(); 
    }
}
