using RuntimeCommandRouter;
using System.Reflection;
internal static class Contracts
{
    public static void Main()
    {
        if(CommandHandlers.Sum(["x","1"])!="Usage: sum <left> <right>")throw new Exception("parse");
        var flags=BindingFlags.Static|BindingFlags.NonPublic;var type=typeof(RuntimeCommandRouter.Program);
        var invoke=type.GetMethod("InvokeCommand",flags)!;
        var descriptor=new CommandDescriptor("sum","",typeof(CommandHandlers).GetMethod("Sum")!);
        if((string)invoke.Invoke(null,[descriptor,new[]{"2147483647","1"}])! != "Command failed.")throw new Exception("reflection overflow");
        var adapter=type.GetMethod("FormatWithLegacyBoundary",flags)!;
        if(!((string)adapter.Invoke(null,[new object(),"X"])!).StartsWith("Legacy contract error:"))throw new Exception("dynamic rejection");
        var validation=type.GetMethod("ValidateCommandSignature",flags)!;
        try{validation.Invoke(null,[typeof(Contracts).GetMethod(nameof(Bad))!]);throw new Exception("bad signature accepted");}
        catch(TargetInvocationException e) when(e.InnerException is InvalidOperationException){}
    }
    public static int Bad(string[] args)=>args.Length;
}
