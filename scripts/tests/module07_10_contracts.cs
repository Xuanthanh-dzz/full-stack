using System.Reflection;
using System.Runtime.ExceptionServices;
using GraphDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static T Call<T>(string name,params object?[] args){try{return (T)typeof(Program).GetMethod(name,BindingFlags.NonPublic|BindingFlags.Static)!.Invoke(null,args)!;}catch(TargetInvocationException ex) when(ex.InnerException!=null){ExceptionDispatchInfo.Capture(ex.InnerException).Throw();throw;}}
 static void Main(){
var graph=new Graph<string>();graph.AddUndirectedEdge("a","b");graph.AddUndirectedEdge("a","b");Check(graph.VertexCount==2 && graph.Neighbors("a").SequenceEqual(new[]{"b"}) && graph.Neighbors("b").Contains("a"),"undirected idempotent edge");var snapshot=graph.Neighbors("a");graph.AddUndirectedEdge("a","c");Check(snapshot.Count==1,"snapshot isolation");if(snapshot is string[] array)array[0]="bad";Check(!graph.Neighbors("a").Contains("bad"),"caller mutation isolation");Check(graph.Edges().Count()==2,"edge dedup");Throws<KeyNotFoundException>(()=>graph.Neighbors("missing"));
 }
}
