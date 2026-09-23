using System.Reflection;
using System.Runtime.ExceptionServices;
using BinarySearchTreeDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static T Call<T>(string name,params object?[] args){try{return (T)typeof(Program).GetMethod(name,BindingFlags.NonPublic|BindingFlags.Static)!.Invoke(null,args)!;}catch(TargetInvocationException ex) when(ex.InnerException!=null){ExceptionDispatchInfo.Capture(ex.InnerException).Throw();throw;}}
 static void Main(){
var tree=new BinarySearchTree<int>();var model=new SortedSet<int>();var rng=new Random(77);for(int i=0;i<500;i++){int v=rng.Next(-100,100);Check(tree.Add(v)==model.Add(v),"duplicate result");Check(tree.Count==model.Count && tree.InOrder().SequenceEqual(model),"sorted invariant");Check(tree.Contains(v) && !tree.Contains(999),"contains");}var chain=new BinarySearchTree<int>();for(int i=0;i<1000;i++)chain.Add(i);Check(chain.InOrder().SequenceEqual(Enumerable.Range(0,1000)),"skew traversal");Throws<ArgumentNullException>(()=>new BinarySearchTree<string>().Add(null!));
 }
}
