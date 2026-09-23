using System.Reflection;
using System.Runtime.ExceptionServices;
using TrieDemo;
internal static class Contracts
{
 static void Check(bool ok,string why){if(!ok)throw new InvalidOperationException(why);}
 static void Throws<T>(Action action) where T:Exception {try{action();}catch(T){return;}throw new InvalidOperationException("Expected "+typeof(T).Name);}
 static T Call<T>(string name,params object?[] args){try{return (T)typeof(Program).GetMethod(name,BindingFlags.NonPublic|BindingFlags.Static)!.Invoke(null,args)!;}catch(TargetInvocationException ex) when(ex.InnerException!=null){ExceptionDispatchInfo.Capture(ex.InnerException).Throw();throw;}}
 static void Main(){
var trie=new Trie();string[] words={"car","cart","cat","apple","a😀","café","cafe\u0301"};foreach(var w in words){trie.Add(w);trie.Add(w);}Check(trie.Contains(" CAR ") && !trie.Contains("ca"),"word versus prefix");foreach(string p in new[]{"ca","a","z"})foreach(int k in new[]{1,2,20})Check(trie.FindByPrefix(p,k).SequenceEqual(words.Where(x=>x.StartsWith(p,StringComparison.Ordinal)).Order(StringComparer.Ordinal).Take(k)),"prefix oracle");Check(trie.Contains("café") && trie.Contains("cafe\u0301"),"no implicit Unicode composition");Throws<ArgumentException>(()=>trie.Add(" "));Throws<ArgumentOutOfRangeException>(()=>trie.FindByPrefix("c",0));
 }
}
