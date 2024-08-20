package spoon_test;
import spoon_test.App;
import java.io.File;
import java.io.IOException;
import java.io.BufferedReader;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.List;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import org.apache.commons.io.FileUtils;

public class Main{
    public static void main(String args[]) throws IOException {
        System.out.println("Maven Hello World!");
        App test = new App();
        // test.coverageInstrumentor("/spoon_test/test/math/src");
        if(args.length < 1){ // path of java
            System.out.println("Please check your argument: {path_of_java} {...}");
            System.exit(0);
        }
        // traverseFolder("/spoon_test/test/math/src/java");
        if (args[0].equals("callsequence")){
            traverseCallSequence(args[1], args[2], args[3]);
        }
        else if (args[0].equals("fail")){
            traverseFail(args[1], args[2], args[3], args[4], Integer.parseInt(args[5]), Boolean.parseBoolean(args[6]), args[1]);
        }
        else if (args[0].equals("remove")){
            traverseRemove(args[1], args[2], args[3], args[4], Integer.parseInt(args[5]));
        }
        else if (args[0].equals("delete")){
            traverseDelete(args[1], args[2], args[3], args[4], Integer.parseInt(args[5]));
        }
        else if (args[0].equals("branch")){
            traverseBranch(args[1], args[2], args[3], args[1]);
        }
        //traverseFolder(args[0]);
        //File src = new File(args[3]);
        //File dst = new File(args[1]);
        //FileUtils.copyDirectory(src, dst);

    }


    public static void traverseFail(String folderPath, String targetPath, String tmpPath, String branchFileName, int lineNo, boolean cond, String srcPath) throws IOException {
    //public static void traverseFolder(String folderPath) throws IOException {
        File[] files = new File(folderPath).listFiles();
        for(File f : files) {
			if(f.isDirectory()) {
				traverseFail(f.getAbsolutePath(), targetPath, tmpPath, branchFileName, lineNo, cond, srcPath);
				//traverseFolder(f.getAbsolutePath());
			} else {
                String fileName = f.getName();
                if (fileName.equals(branchFileName) && fileName.substring(fileName.lastIndexOf(".") + 1).equals("java")) {
                    //File newFile = new File(tmpPath + "/" + f.getName());

                    //Files.copy(f.toPath(), newFile.toPath(), StandardCopyOption.REPLACE_EXISTING);
                    //System.out.println(f.getAbsolutePath());
                    App test = new App();
                    try {
				        test.conditionInstrumentor(f.getAbsolutePath(), targetPath, cond, lineNo, srcPath);
                        //f.delete();
				        //test.branchInstrumentor(newFile.getAbsolutePath());
                        //Files.copy(newFile.toPath(), f.toPath(), StandardCopyOption.REPLACE_EXISTING);
                        //newFile.delete();
                    } catch (Exception e) {
                    }
                }
			}
		}
    }

    
    public static void traverseDelete(String folderPath, String targetPath, String tmpPath, String stmtFileName, int lineNo) throws IOException {
    //public static void traverseFolder(String folderPath) throws IOException {
        File[] files = new File(folderPath).listFiles();
        for(File f : files) {
			if(f.isDirectory()) {
				traverseDelete(f.getAbsolutePath(), targetPath, tmpPath, stmtFileName, lineNo);
				//traverseFolder(f.getAbsolutePath());
			} else {
                String fileName = f.getName();
                if (fileName.equals(stmtFileName) && fileName.substring(fileName.lastIndexOf(".") + 1).equals("java")) {
                    File newFile = new File(tmpPath + "/" + f.getName());

                    Files.copy(f.toPath(), newFile.toPath(), StandardCopyOption.REPLACE_EXISTING);
                    //System.out.println(f.getAbsolutePath());
                    App test = new App();
                    try {
				        test.stmtDeleter(newFile.getAbsolutePath(), targetPath, lineNo);
                        f.delete();
				        //test.branchInstrumentor(newFile.getAbsolutePath());
                        Files.copy(newFile.toPath(), f.toPath(), StandardCopyOption.REPLACE_EXISTING);
                        newFile.delete();
                    } catch (Exception e) {
                    }
                }
			}
		}
    }

    public static void traverseRemove(String folderPath, String targetPath, String tmpPath, String branchFileName, int lineNo) throws IOException {
    //public static void traverseFolder(String folderPath) throws IOException {
        File[] files = new File(folderPath).listFiles();
        for(File f : files) {
			if(f.isDirectory()) {
				traverseRemove(f.getAbsolutePath(), targetPath, tmpPath, branchFileName, lineNo);
				//traverseFolder(f.getAbsolutePath());
			} else {
                String fileName = f.getName();
                if (fileName.equals(branchFileName) && fileName.substring(fileName.lastIndexOf(".") + 1).equals("java")) {
                    File newFile = new File(tmpPath + "/" + f.getName());

                    Files.copy(f.toPath(), newFile.toPath(), StandardCopyOption.REPLACE_EXISTING);
                    //System.out.println(f.getAbsolutePath());
                    App test = new App();
                    try {
				        test.conditionRemover(newFile.getAbsolutePath(), targetPath, lineNo);
                        f.delete();
				        //test.branchInstrumentor(newFile.getAbsolutePath());
                        Files.copy(newFile.toPath(), f.toPath(), StandardCopyOption.REPLACE_EXISTING);
                        newFile.delete();
                    } catch (Exception e) {
                    }
                }
			}
		}
    }

    public static void traverseCallSequence(String folderPath, String targetPath, String tmpPath) throws IOException {
        File[] files = new File(folderPath).listFiles();
        for(File f : files) {
			if(f.isDirectory()) {
				traverseCallSequence(f.getAbsolutePath(), targetPath, tmpPath);
			} else {
                String fileName = f.getName();
                if (fileName.substring(fileName.lastIndexOf(".") + 1).equals("java")) {
                    File newFile = new File(tmpPath + "/" + f.getName());

                    Files.copy(f.toPath(), newFile.toPath(), StandardCopyOption.REPLACE_EXISTING);
                    //System.out.println(f.getAbsolutePath());
                    App test = new App();
                    try {
				        test.coverageInstrumentor(newFile.getAbsolutePath(), targetPath);
                        f.delete();
				    //test.branchInstrumentor(newFile.getAbsolutePath());
                        Files.copy(newFile.toPath(), f.toPath(), StandardCopyOption.REPLACE_EXISTING);
                        newFile.delete();
                    } catch (Exception e) {
                    }
                }
			}
		}
    }
    public static void traverseBranch(String folderPath, String targetPath, String tmpPath, String srcPath) throws IOException {
        File[] files = new File(folderPath).listFiles();
        for(File f : files) {
			if(f.isDirectory()) {
				traverseBranch(f.getAbsolutePath(), targetPath, tmpPath, srcPath);
			} else {
                String fileName = f.getName();
                if (fileName.equals("PeepholeSubstituteAlternateSyntax.java") || fileName.equals("NodeUtil.java") || fileName.equals("CollapseProperties.java") || fileName.equals("CodeGenerator.java") || fileName.equals("RegExpTree.java") || fileName.equals("JsonML.java") || fileName.equals("Scanner.java") || fileName.equals("LineNumberTable.java") || fileName.equals("ObjArray.java") || fileName.equals("SideEffectsAnalysis.java")){/* || fileName.equals("CheckGlobalNames.java") || fileName.equals("JSModule.java") || fileName.equals("NodeTraversal.java") || fileName.equals("Compiler.java")) {*/
		continue;
		}
		if (fileName.substring(fileName.lastIndexOf(".") + 1).equals("java")) {
                    //File newFile = new File(tmpPath + "/" + f.getName());

                    //Files.copy(f.toPath(), newFile.toPath(), StandardCopyOption.REPLACE_EXISTING);
                    //System.out.println(f.getAbsolutePath());
                    App test = new App();
                    //System.out.println(f.getAbsolutePath());
                    try {
				        test.branchInstrumentor(f.getAbsolutePath(), targetPath, srcPath);
				        //test.branchInstrumentor(newFile.getAbsolutePath(), targetPath);
                        //f.delete();
				    //test.branchInstrumentor(newFile.getAbsolutePath());
                        //Files.copy(newFile.toPath(), f.toPath(), StandardCopyOption.REPLACE_EXISTING);
                        //newFile.delete();
                    } catch (Exception e) {  
                    }
                }
			}
		}
    }
}
