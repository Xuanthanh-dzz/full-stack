using System.Reflection;
using System.Runtime.ExceptionServices;
using GraphTraversalDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static T Call<T>(string name,params object?[] args){try{return (T)typeof(Program).GetMethod(name,BindingFlags.NonPublic|BindingFlags.Static)!.Invoke(null,args)!;}catch(TargetInvocationException ex) when(ex.InnerException!=null){ExceptionDispatchInfo.Capture(ex.InnerException).Throw();throw;}}
 static void Main(){
Check(Call<IReadOnlyList<string>>("Bfs","A").SequenceEqual(new[]{"A","B","C","D","E","F"}),"BFS order");Check(Call<IReadOnlyList<string>>("Dfs","A").Distinct().Count()==6,"DFS visits once");Check(Call<IReadOnlyList<string>>("ShortestPath","A","A").SequenceEqual(new[]{"A"}),"identity path");var g=(Dictionary<string,string[]>)typeof(Program).GetField("Graph",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static)!.GetValue(null)!;g["Z"]=Array.Empty<string>();Check(Call<IReadOnlyList<string>>("ShortestPath","A","Z").Count==0,"unreachable");g["F"]=new[]{"A","F"};Check(Call<IReadOnlyList<string>>("Bfs","A").Count==6 && Call<IReadOnlyList<string>>("Dfs","A").Count==6,"cycles");
 }
}
